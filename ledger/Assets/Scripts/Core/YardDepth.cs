using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Ledger.Core
{
    /// HOW DEEP THE BACK YARDS ACTUALLY ARE, AS A DISTRIBUTION OVER SITES —
    /// the printer whose series decides whether the fence variants are a
    /// CONTENT problem or a PROBE problem. It sets no bound and must not
    /// grow one.
    ///
    /// WHY IT EXISTS. The landed verdict at `71316fa` read
    /// `yard_fence/1x1:163/0 1x2:0/0 1x3:0/0 1x4:3/0`: 163 of 166 placements
    /// are the shortest 3.52m panel, the two mid-length variants placed
    /// NOTHING, and the longest placed three. 163 identical panels down every
    /// alley is the repeating boundary the visual bar exists to kill. Which
    /// model is even legal at a site is `StreetDressing.PickFence`'s call and
    /// it turns on ONE number — the yard depth `YardOf` probes off the built
    /// masses — and that number has never been printed. Two completely
    /// different repairs sit behind the same reading:
    ///
    ///   * the yards genuinely cluster shallow, and the fix is CONTENT — more
    ///     short-panel forms, or a different model;
    ///   * the probe misreads deep yards as shallow, and the fix is the PROBE.
    ///
    /// Only the distribution tells those apart, which is why this ships before
    /// anybody touches the placement or the thresholds (rule 2: the printer
    /// first, the series from real runs, the number last).
    ///
    /// IT IS NOT A `KitDressing` AMOUNT ROW, AND THE REASON IS THE POPULATION.
    /// `Measured("yard_fence", runM)` is filed AFTER a model stands up, so its
    /// samples are placements. The sites that matter most here place nothing
    /// at all: a block whose faces the probe could not read never reaches a
    /// pick, and a block banded shallow places the short panel and files a
    /// 3.52 that says nothing about the yard. A distribution over SITES cannot
    /// be recovered from a channel that only sees successful placements, which
    /// is the same reason `Skyline` exists beside the placement counters — its
    /// eight blocks over open sea were all "placed".
    ///
    /// WHAT STATISTIC EVERY NUMBER HERE IS, said plainly, because a number
    /// keeps its name when the question it answers moves:
    ///
    ///   Series      the SORTED DEPTHS THEMSELVES, one per block the probe
    ///               measured, DEEPEST FIRST. Not a summary. Deepest first
    ///               because the question is "are there ANY deep yards",
    ///               which is a max-and-count question and never a median
    ///               one — a median over sites cannot see a minority of deep
    ///               yards however severe, the way `crowdGapMedian=0.41`
    ///               called a street healthy with thirty people shoulder to
    ///               shoulder in it. The cap therefore eats the SHALLOW end,
    ///               and says so when it bites.
    ///   Spread      min .. median .. max over the same population. The
    ///               median answers "is this normal" and the max answers "did
    ///               it ever", and neither answers the other's question, so
    ///               all three print (`billboardStale` read median 0.000 with
    ///               38 of 57 stale and a worst of 116.9 degrees).
    ///   Bands       a COUNT per band over every block WALKED, which is the
    ///               denominator the series does not carry: a block whose
    ///               faces could not be read contributes no depth at all, so
    ///               `n` on the series and `n` on the bands are different
    ///               populations on purpose and both are printed.
    ///   ByDistrict  min/median/max, the DEEP COUNT, and measured-of-walked
    ///               per district. Per district because that is the axis the
    ///               depth actually varies on: `TerraceBlock` caps each row at
    ///               `(blockDepth - 3) / 2`, block depth is a district
    ///               property, and the design note predicts a clean split
    ///               (Hook/Copper/Parade/Exchange shallow, Fairview/Gullwing/
    ///               Ironside deep). The DEEP COUNT is there because a
    ///               per-district median has the same blind spot as the
    ///               global one.
    ///   Deepest     the deepest site's district and map position beside its
    ///               depth — one entry carrying value and place, so the next
    ///               reader opens one block rather than fifty-two.
    ///   ProbeWhy    a COUNT per reason the probe returned nothing, over
    ///               measured-of-walked. This is the datum-exists half of a
    ///               placement metric: distance to the datum is the easy half
    ///               and whether the datum is there at all is the half that
    ///               caught eight blocks hanging over open sea.
    ///   PickBy      a COUNT per chosen-variant x band, over SLOTS AT THE
    ///               MOMENT THE MODEL WAS CHOSEN. A DIFFERENT POPULATION FROM
    ///               `kitByVariant`, which counts what was PLACED — a pick is
    ///               filed before the placement roll and before the geometry
    ///               refusal, so `yardPickBy` is always the larger and the two
    ///               must not be read as one. It exists because the variant
    ///               choice turns on TWO inputs, not one: the yard depth AND
    ///               the run left on the tile. Without it, "1x2 placed zero"
    ///               cannot distinguish a shallow yard from a deep yard with
    ///               no room left, and those have different fixes too.
    ///
    /// THE BANDS COME FROM THE LIVE CONSTANTS, PASSED IN ONCE. `Cuts` takes
    /// `StreetDressing`'s own `1.5f` and `DeepYard`, so the banding cannot
    /// drift away from the thresholds the placement actually uses — one idea,
    /// one implementation, and no copy of the arithmetic in this file to fall
    /// out of step. A run where nobody called `Cuts` prints the WORD
    /// `cuts-unset` in every banded key rather than banding against a default
    /// that would look exactly like a measurement.
    ///
    /// NOTHING HERE IS A THRESHOLD. The band edges are the placement's own
    /// decision boundary being REPORTED, not a bound being set: no key goes
    /// red, no key is compared against anything. The only numbers chosen in
    /// this file are the two PRINT CAPS, and both announce themselves the
    /// moment they bite.
    ///
    /// EVERY KEY IS A WHOLE-RUN CUMULATIVE COUNT over the one dressing pass,
    /// read at the end of the run on the DONE LINE. Nothing here may be
    /// emitted on a screenshot line: a cumulative number sampled where a shot
    /// happens freezes at the last shot while its neighbours keep climbing,
    /// which is how `namesManagedEver` printed 28 ever-managed beside 44
    /// offered in one frame and cost an afternoon.
    public sealed class YardDepth
    {
        /// One block the probe walked. `Depth` is meaningful only when
        /// `Measured` is true — a block whose faces gave no back of row has no
        /// depth, and filing a 0 for it would put a fabricated sample in the
        /// series (a constant is not a measurement).
        struct Site
        {
            public string District, Why;
            public double X, Z;
            public float Depth;
            public bool Measured;
        }

        readonly List<Site> _sites = new List<Site>();
        /// Chosen variant x band, keyed `<variant>/<band>`. Ordinal, so two
        /// runs diff by eye.
        readonly Dictionary<string, long> _picks = new Dictionary<string, long>();
        long _slots;

        float _minYard, _deepYard;
        bool _cutsSet;

        /// HOW MANY DEPTHS THE SERIES PRINTS before it says `+Nmore`. Not a
        /// measured threshold and not a gate — a print bound. Forty is above
        /// the fifty-two blocks this map has today at the deep end, so on a
        /// live run it does not bite at all; when a bigger map makes it bite
        /// it eats the SHALLOW tail, because the deep end is the end the
        /// question is about.
        const int SeriesCap = 40;

        /// HOW MANY DISTRICT ROWS print before `+Nmore`. Seven districts today
        /// plus headroom for the `nowhere` row a block off the district
        /// rectangles produces, and for districts nobody has added yet.
        const int DistrictCap = 16;

        const string NothingMeasured = "nothing-measured";
        const string CutsUnset = "cuts-unset";

        // ---- WHAT THE PROBE FILES -----------------------------------------

        /// The two live band edges, from the placement's own constants. Called
        /// once, before the walk. Passing them rather than copying them is the
        /// whole point: a second copy of a threshold is the site nobody
        /// updates.
        public void Cuts(float minYard, float deepYard)
        {
            _minYard = minYard;
            _deepYard = deepYard;
            _cutsSet = true;
        }

        /// One block walked, whatever the outcome. `measured` says whether a
        /// depth was computed at all; `why` names the reason it was not, and
        /// is ignored when it was. Called for EVERY block — a block the probe
        /// skipped is the case the whole denominator exists to make visible.
        public void Walked(string district, double x, double z,
                           bool measured, float depth, string why)
        {
            _sites.Add(new Site
            {
                District = Name(district),
                Why = KitDressing.Safe(why),
                X = x,
                Z = z,
                Depth = depth,
                Measured = measured && !float.IsNaN(depth) && !float.IsInfinity(depth),
            });
        }

        /// One fence slot at the instant its model was chosen, with the depth
        /// that chose it. `chose` is the kit variant or null when nothing
        /// fitted. Filed BEFORE the placement roll and BEFORE the geometry
        /// refusal, so this population is larger than the placed one by
        /// construction — see the class note.
        public void Picked(float depth, string chose)
        {
            _slots++;
            var v = KitDressing.Safe(chose);
            if (v.Length == 0) v = "none";
            var k = v + "/" + Band(depth);
            long n;
            _picks[k] = (_picks.TryGetValue(k, out n) ? n : 0) + 1;
        }

        /// Blocks walked this run, whatever the probe made of them.
        public int Count { get { return _sites.Count; } }

        // ---- THE DONE-LINE VALUES -----------------------------------------

        /// `<minYard>/<deepYard>` — the live band edges, so the band NAMES
        /// have their numbers on the same line and a reader need not open the
        /// Game layer to know what `deep` meant on this run. The word when
        /// nobody set them, which is a wiring fault and must not read as a
        /// measurement.
        public string CutsRow()
        {
            if (!_cutsSet) return CutsUnset;
            return F(_minYard) + "/" + F(_deepYard);
        }

        /// `[12.40/9.20/6.51/.../3.20/+Nmore]/n39` — THE SERIES, deepest first,
        /// one entry per block the probe measured. The trailing `n` is that
        /// population; `Bands()` carries the blocks WALKED, which is a bigger
        /// number, and the two are printed separately on purpose.
        public string Series()
        {
            var v = Measured();
            if (v.Count == 0) return "[" + NothingMeasured + "]/n0";
            v.Sort();
            var sb = new StringBuilder("[");
            int shown = v.Count < SeriesCap ? v.Count : SeriesCap;
            for (int i = 0; i < shown; i++)
            {
                if (i > 0) sb.Append('/');
                sb.Append(F(v[v.Count - 1 - i]));
            }
            if (v.Count > shown)
                sb.Append("/+").Append(N(v.Count - shown)).Append("more");
            return sb.Append("]/n").Append(N(v.Count)).ToString();
        }

        /// `<min>..<median>..<max>/n39`. The same population as `Series` and
        /// therefore the same variable printed twice — a summary a reader can
        /// quote without counting, not a second measurement, and it cannot
        /// disagree with the series above it.
        public string Spread()
        {
            var v = Measured();
            if (v.Count == 0) return NothingMeasured + "/n0";
            v.Sort();
            return F(v[0]) + ".." + F(Median(v)) + ".." + F(v[v.Count - 1])
                 + "/n" + N(v.Count);
        }

        /// `[noback:6,nogap:2,alley:37,deep:3]/n48` — the legality census over
        /// every block WALKED, at the placement's own cut points. Every band
        /// prints every run, including the empty ones, so "no deep yards in
        /// this city" and "the deep band was never computed" cannot read the
        /// same way.
        ///
        ///   noback  the probe found no back of row on one of the two faces,
        ///           so there is no depth at all — no fence is offered here.
        ///   nogap   a depth under `minYard`: a party-wall gap, not a yard.
        ///   alley   a yard, but under `deepYard` — only the straight 3.52m
        ///           panel is legal, which is the reading under test.
        ///   deep    the U-shaped runs are legal here.
        public string Bands()
        {
            if (!_cutsSet) return "[" + CutsUnset + "]/n" + N(_sites.Count);
            long noback = 0, nogap = 0, alley = 0, deep = 0;
            foreach (var s in _sites)
            {
                if (!s.Measured) { noback++; continue; }
                if (s.Depth < _minYard) nogap++;
                else if (s.Depth < _deepYard) alley++;
                else deep++;
            }
            return "[noback:" + N(noback) + ",nogap:" + N(nogap)
                 + ",alley:" + N(alley) + ",deep:" + N(deep)
                 + "]/n" + N(_sites.Count);
        }

        /// `[copper_row:3.20..3.60..3.60/0deep/14of14,...]` — per district:
        /// the spread, the count in the DEEP band, and measured-of-walked.
        /// Ordinal by district. A district that was walked and never measured
        /// prints `nothing-measured/0deep/0of6`, which is a finding rather
        /// than an absence.
        public string ByDistrict()
        {
            if (_sites.Count == 0) return "[" + NothingMeasured + "]";
            var names = new SortedDictionary<string, bool>(System.StringComparer.Ordinal);
            foreach (var s in _sites) names[s.District] = true;

            var rows = new List<string>();
            foreach (var name in names.Keys)
            {
                var v = new List<float>();
                int walked = 0; long deep = 0;
                foreach (var s in _sites)
                {
                    if (s.District != name) continue;
                    walked++;
                    if (!s.Measured) continue;
                    v.Add(s.Depth);
                    if (_cutsSet && s.Depth >= _deepYard) deep++;
                }
                v.Sort();
                var cell = v.Count == 0
                    ? NothingMeasured
                    : F(v[0]) + ".." + F(Median(v)) + ".." + F(v[v.Count - 1]);
                rows.Add(name + ":" + cell
                         + "/" + (_cutsSet ? N(deep) + "deep" : CutsUnset)
                         + "/" + N(v.Count) + "of" + N(walked));
            }
            return Capped(rows, DistrictCap);
        }

        /// `<district>@<x>,<z>/<depth>` — the deepest yard measured, and where
        /// to stand to look at it. A worst with no place sends the next reader
        /// through every block on the map.
        public string Deepest()
        {
            bool any = false;
            Site pick = default(Site);
            foreach (var s in _sites)
            {
                if (!s.Measured) continue;
                if (!any || s.Depth > pick.Depth) { pick = s; any = true; }
            }
            if (!any) return NothingMeasured;
            return pick.District + "@" + N0(pick.X) + "," + N0(pick.Z)
                 + "/" + F(pick.Depth);
        }

        /// `[no_back_lo:4,no_back_hi:2]/39of48` — why the probe produced no
        /// depth, keyed by the reason the caller named, over
        /// measured-of-walked. `[none]/39of48` is a clean run; `[none]/0of48`
        /// is forty-eight blocks that produced neither a depth nor a reason,
        /// which is not a clean result but a probe that filed nothing.
        public string ProbeWhy()
        {
            var tally = new SortedDictionary<string, long>(System.StringComparer.Ordinal);
            int measured = 0;
            foreach (var s in _sites)
            {
                if (s.Measured) { measured++; continue; }
                var k = s.Why.Length > 0 ? s.Why : "unnamed";
                long n;
                tally.TryGetValue(k, out n);
                tally[k] = n + 1;
            }
            var rows = new List<string>();
            foreach (var kv in tally) rows.Add(kv.Key + ":" + N(kv.Value));
            return Capped(rows, DistrictCap)
                 + "/" + N(measured) + "of" + N(_sites.Count);
        }

        /// `[1x1/alley:160,1x1/deep:1,1x4/deep:3,none/alley:12]/n176` — every
        /// slot at the instant its model was chosen, crossed with the band of
        /// the yard that chose it. THE KEY THAT SEPARATES THE TWO CAUSES OF A
        /// SHORT PANEL: `1x1/alley` is a shallow yard and `1x1/deep` is a deep
        /// yard with no run left, and no count of placements can tell them
        /// apart. `none/*` is a slot where nothing fitted at all, which ends
        /// the tiling for that block.
        ///
        /// NOT `kitByVariant`. That counts placements; this counts picks,
        /// before the share roll and before the geometry refusal. They are
        /// different populations and the difference between them is itself a
        /// reading.
        public string PickBy()
        {
            var rows = new List<string>();
            foreach (var kv in Ordered(_picks)) rows.Add(kv.Key + ":" + N(kv.Value));
            if (rows.Count == 0) return "[" + NothingMeasured + "]/n" + N(_slots);
            return Capped(rows, DistrictCap) + "/n" + N(_slots);
        }

        // ---- PLUMBING -----------------------------------------------------

        /// Which band a depth falls in, from the LIVE cuts. The one place the
        /// band arithmetic exists; `Bands` and `Picked` both come here rather
        /// than each carrying a copy of the comparison.
        string Band(float depth)
        {
            if (!_cutsSet) return CutsUnset;
            if (float.IsNaN(depth) || float.IsInfinity(depth)) return "unreadable";
            if (depth < _minYard) return "nogap";
            return depth < _deepYard ? "alley" : "deep";
        }

        List<float> Measured()
        {
            var v = new List<float>();
            foreach (var s in _sites) if (s.Measured) v.Add(s.Depth);
            return v;
        }

        static float Median(List<float> sorted)
        {
            return sorted.Count % 2 == 1
                ? sorted[sorted.Count / 2]
                : (sorted[sorted.Count / 2 - 1] + sorted[sorted.Count / 2]) * 0.5f;
        }

        /// A row list, bracketed, capped, and SAYING SO when the cap bites. A
        /// truncation that does not announce itself reads as a finding — the
        /// `| head -3` on the character audit read as three of five bodies
        /// failing when nothing was broken.
        static string Capped(List<string> rows, int cap)
        {
            if (rows.Count == 0) return "[none]";
            var sb = new StringBuilder("[");
            int shown = rows.Count < cap ? rows.Count : cap;
            for (int i = 0; i < shown; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append(rows[i]);
            }
            if (rows.Count > shown) sb.Append(",+").Append(N(rows.Count - shown)).Append("more");
            return sb.Append(']').ToString();
        }

        /// A DISTRICT NAME IS PROSE — `Copper Row`, `the Hook` — and the
        /// verdict is space-separated `key=value`, so an unfolded name
        /// truncates the whole value silently at the space
        /// (`crowdBodyWidth=0.45(narrowest 0.39 broadest 0.53)` came back as
        /// `0.45(narrowest`). Folded through `KitDressing.Safe`, which is the
        /// one implementation of this idea in Core, rather than a second copy
        /// here that would drift. A block off every district rectangle gets
        /// the WORD `nowhere`, because a blank district row and a district
        /// called nothing are different facts.
        static string Name(string district)
        {
            var n = KitDressing.Safe(district);
            return n.Length == 0 ? "nowhere" : n;
        }

        static SortedDictionary<string, long> Ordered(Dictionary<string, long> src)
        {
            var s = new SortedDictionary<string, long>(System.StringComparer.Ordinal);
            foreach (var kv in src) s[kv.Key] = kv.Value;
            return s;
        }

        static string F(double v) { return v.ToString("0.00", CultureInfo.InvariantCulture); }
        static string N0(double v) { return v.ToString("0", CultureInfo.InvariantCulture); }
        static string N(long v) { return v.ToString(CultureInfo.InvariantCulture); }
        static string N(int v) { return v.ToString(CultureInfo.InvariantCulture); }
    }
}
