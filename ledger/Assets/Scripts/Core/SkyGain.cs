using System.Collections.Generic;
using System.Globalization;

namespace Ledger.Core
{
    /// RENDERED-OVER-AUTHORED FOR THE SKY, AND THE THREE COMPARATOR BANDS
    /// WITHOUT WHICH IT CANNOT DISCRIMINATE ANYTHING.
    ///
    /// WHY IT EXISTS. On `c03ead2`, across 15 of 15 dry camera rows,
    /// `sky>lit` FAILS and the other two rungs hold — `lit>gnd` on the
    /// re-aimed cameras and `gnd>shd` everywhere. Two hypotheses were on the
    /// table and no landed number could separate them:
    ///
    ///   (a) THE DAYLIGHT PATH IS SCALED WRONG — aperture, exposure, the
    ///       common multiplier. Everything in frame scales together.
    ///   (b) THE SKY DOME IS AUTHORED (or shaded) TOO DARK — only the sky
    ///       band is wrong; wall and ground are as intended.
    ///
    /// THE TWO READINGS THAT MOVE OPPOSITE WAYS, said here so the next reader
    /// cannot take a number and pick a preferred conclusion from it:
    ///
    ///   `xgrade` = graded / raw, PER BAND. This is the COMMON PATH and
    ///     nothing else: numerator and denominator are the SAME rays of the
    ///     SAME scene at the SAME instant with `FilmGrade.Bypass` toggled, so
    ///     every scene-referred term cancels and what is left is exposure,
    ///     the ACES curve, bloom, vignette and grain. If `xgrade` on `sky` is
    ///     of the same size as `xgrade` on `lit` and `gnd`, the common path
    ///     treats the sky like everything else and hypothesis (a) CANNOT be
    ///     sky-specific. If `xgrade` on `sky` is far smaller than on the
    ///     geometry bands, the grade is where the sky loses its place.
    ///
    ///   `xsrc` = rendered / source, PER BAND, and IT ASKS A DIFFERENT
    ///     QUESTION ON THE SKY ROW THAN ON THE OTHER THREE. On `sky` the
    ///     source is the DOME COLOUR THE MATERIAL ACTUALLY HELD at this ray's
    ///     elevation, and the dome is an emission with no lighting in it — so
    ///     on the RAW arm `xsrc` is a pure transfer that reads 1.000 when the
    ///     dome puts on screen what was written into it. On `lit`, `gnd` and
    ///     `shd` the source is the material ALBEDO and `xsrc` therefore
    ///     contains the whole irradiance. A SKY ROW AND A GROUND ROW MAY NOT
    ///     BE COMPARED ON `xsrc`; that comparison is what `xgrade` is for.
    ///
    /// So the discriminator is a pair, not a number:
    ///
    ///   raw `xsrc` on sky ~= 1.000 and `xgrade` even across bands
    ///        => the dome renders what it was authored, the common path is
    ///           even-handed, and the SKY'S AUTHORED VALUE is the subject.
    ///           That is (b), and the address is whichever stop the rays
    ///           actually sample — read `skyGainByElev`, not this row.
    ///   raw `xsrc` on sky far from 1.000, roughly constant across elevation
    ///        => a scalar sitting on the dome alone.
    ///   raw `xsrc` on sky far from 1.000 and CLIMBING with elevation
    ///        => a power law, not a scalar: the signature of a colour-space
    ///           conversion applied twice (or not at all) between
    ///           `SceneLighting.C()` and the shader. SUSPECT THE PLUMBING,
    ///           NOT THE ART — and the fix is at the funnel, not at
    ///           `LightModel.SkyColour`.
    ///   `xgrade` on sky far below `xgrade` on gnd and lit
    ///        => (a), and sky-specific: the common path is not common.
    ///
    /// WHAT STATISTIC EACH NUMBER IS, because it is the one thing a reader
    /// cannot recover from the number:
    ///
    ///   gr, rw, sc   RAY-WEIGHTED MEANS over every admitted ray of every
    ///                LANDED shot in this regime. Not medians, not peaks, not
    ///                per shot. `ValuePanel`'s band values are MEDIANS PER
    ///                SHOT in the DISPLAY-referred space; these are MEANS
    ///                OVER A REGIME in LINEAR. The two are not
    ///                interchangeable and must never be quoted as one
    ///                reading — `valueBands` answers "how does this frame
    ///                look", this answers "what did the path do to it".
    ///   xgrade,xsrc  RATIOS OF MEANS, not means of ratios — the same choice
    ///                `GroundGain` makes and for the same reason: it stays
    ///                exact when the rays behind a row carry different
    ///                sources.
    ///   vig          the RAY-WEIGHTED MEAN of `LightModel.VignetteAt` over
    ///                the same rays. It is not a measurement of the frame; it
    ///                is what the grade's vignette WILL have multiplied that
    ///                band by, computed from the ray's own viewport position
    ///                through the function that mirrors the shader. It is
    ///                here because "the sky sits at the top of the frame
    ///                where the vignette bites" is a cheap alternative
    ///                explanation and it should be ruled in or out by a
    ///                printed number rather than by argument.
    ///   @n/rn/sn     the rays each mean is a mean OF: admitted, with a raw
    ///                twin, with a known source (rule 3b — every zero ships
    ///                its denominator).
    ///
    /// EVERYTHING HERE IS LINEAR, and that is deliberate rather than
    /// convenient. `GroundGain` is linear, so its `groundGainByRaw` rows and
    /// this key's `gnd` row are in one space and can be read against each
    /// other. This class does NO conversion and cannot check one — it is
    /// arithmetic on whatever it is handed, exactly like `GroundGain`, and
    /// the caller's comment names the space. THE TRAP IS WRITTEN DOWN IN
    /// ADVANCE: an `xsrc` near 2.05..2.09 on a GEOMETRY band is the
    /// gamma/linear mismatch `GroundGain` names, not a lighting gain.
    ///
    /// EVERY ROW CARRIES THE REGIME IT WAS TAKEN IN AND A READER MAY NOT
    /// COMPARE ACROSS TWO. The tag is `ValuePanel`'s own `WeatherTag` — one
    /// implementation, called, not copied — with a NIGHT term appended.
    /// Weather alone is not enough here: a dry midnight and a dry noon both
    /// tag `r0.00w0.00`, the sky band between them differs by an order of
    /// magnitude, and pooling them would be `bodyReadWhen`'s fault exactly
    /// (35.7 against 10.8, noon against midnight, quoted side by side).
    ///
    /// IT HOLDS NO CLASSIFIER, NO GEOMETRY TEST AND NO BOUND. Which band a
    /// ray is in, what its material albedo is, whether the ungraded twin
    /// rendered, and what the dome material held are all the caller's — they
    /// need a hit normal, a sun vector and a live `Material`, none of which
    /// exist in Core. NOTHING HERE COMPARES AGAINST A CONSTANT and nothing
    /// returns a pass/fail: every method is a printer. The bound comes after
    /// the series, in that order (rule 2).
    ///
    /// IT LIVES IN CORE for the reason `GroundGain` and `ValuePanel` do: the
    /// Game layer does not compile in this container, so a formatter written
    /// there ships UNRUN, and an unrun formatter printing a plausible string
    /// is the silent-instrument failure this project keeps paying for.
    public sealed class SkyGain
    {
        /// The bands, in `ValuePanel`'s own numbering so a ray classified
        /// once can be filed in both without a translation table. `Other` is
        /// counted and never given a row: a parked car and a sloped roof have
        /// no authored value this instrument could divide by, and a row
        /// pooling them would be a mean of nothing in particular.
        public const int Sky = 0, LitWall = 1, Ground = 2, Shadow = 3, Other = 4;
        public const int BandCount = 5;

        static readonly string[] BandNames = { "sky", "lit", "gnd", "shd", "oth" };

        /// THE ELEVATION LADDER'S RUNGS, IN DEGREES ABOVE THE HORIZON. These
        /// are a HISTOGRAM AXIS, not thresholds: nothing compares against
        /// them, no gate reads them, and moving one changes which rows exist
        /// rather than which answer is given. They are geometric — the dome's
        /// gradient is `pow(sin(elev), curve)`, which does almost all of its
        /// moving in the first ten degrees, so the rungs are packed there.
        ///
        /// THE LADDER IS THE POINT, not a decoration. A single "sky gain"
        /// would be a mean over whatever slice of dome the camera happened to
        /// frame, and the landed evidence already says that slice decides the
        /// number: on `c03ead2`, in one run at one regime, the aerial rows
        /// read sky 0.368..0.440 and the street rows 0.591..0.696. Rungs from
        /// the same run, same vantage class, one contributor varied.
        static readonly double[] ElevEdge = { 0, 2, 5, 10, 20, 45 };
        static readonly string[] ElevName =
            { "below0", "e00..02", "e02..05", "e05..10", "e10..20", "e20..45", "e45..90" };

        /// Rows are capped and the cap ANNOUNCES ITSELF, because an
        /// unannounced truncation reads as a finding.
        public const int RowCap = 32;
        public const int ListCap = 12;

        sealed class Reg
        {
            internal readonly string Tag;
            internal readonly double[] Gr = new double[BandCount];
            internal readonly double[] Rw = new double[BandCount];
            internal readonly double[] Sc = new double[BandCount];
            internal readonly double[] Vg = new double[BandCount];
            internal readonly long[] N = new long[BandCount];
            internal readonly long[] RwN = new long[BandCount];
            internal readonly long[] ScN = new long[BandCount];
            internal long Shots, ShotsWithTwin, ShotsSkyboxLive;

            // The dome stops this regime was photographed under. Min and max
            // rather than a mean: `top`, `hor` and `gnd` are deterministic
            // functions of (night, rain) and so are CONSTANT inside a tag by
            // construction, while `cover` is seeded off the calendar day and
            // is not. Printing min..max makes that difference visible instead
            // of assumed — if a stop that should be constant prints a spread,
            // the tag is not the regime it claims to be.
            internal readonly double[] StopLo = new double[StopCount];
            internal readonly double[] StopHi = new double[StopCount];
            internal bool StopsSeen;

            // The elevation ladder, per regime. Kept for every regime so the
            // choice of WHICH ladder to print is made at emit time from the
            // ray counts, rather than by a caller guessing which regime will
            // turn out to matter.
            internal readonly double[] EGr;
            internal readonly double[] ERw;
            internal readonly double[] ESc;
            internal readonly long[] EN;
            internal readonly long[] ERwN;
            internal readonly long[] EScN;

            internal Reg(string tag)
            {
                Tag = tag;
                int b = ElevName.Length;
                EGr = new double[b]; ERw = new double[b]; ESc = new double[b];
                EN = new long[b]; ERwN = new long[b]; EScN = new long[b];
                for (int i = 0; i < StopCount; i++) { StopLo[i] = double.MaxValue; StopHi[i] = double.MinValue; }
            }

            internal long Rays
            {
                get { long t = 0; for (int i = 0; i < BandCount; i++) t += N[i]; return t; }
            }
        }

        /// The dome's authored stops, in the order they are printed. `cover`
        /// and `glow` are not colours and are printed raw; they are here
        /// because the gradient mirror below does NOT model the cloud layer
        /// or the sun glow, and a reader bounding that omission needs to know
        /// how much of the dome they cover and how hard they push.
        public const int StopTop = 0, StopHor = 1, StopGnd = 2, StopCloud = 3,
                         StopCover = 4, StopGlow = 5, StopCount = 6;
        static readonly string[] StopNames = { "top", "hor", "gnd", "cloud", "cover", "glow" };

        readonly List<string> _regSeen = new List<string>();
        readonly Dictionary<string, Reg> _regs = new Dictionary<string, Reg>();
        long _shotsOffered, _shotsMeasured, _shotsWithTwin, _shotsSkyboxLive;
        readonly long[] _rays = new long[BandCount];

        /// ONE SHOT'S RAYS. Opened at the shot, closed at the shot, so a row
        /// cannot be assembled out of two different frames — `ValuePanel`'s
        /// rule and `GroundGain`'s, kept rather than re-argued.
        public sealed class ShotAcc
        {
            internal readonly string Tag;
            internal readonly bool RawTwin, SkyboxLive;
            internal readonly double[] Stops = new double[StopCount];
            internal readonly bool StopsKnown;

            internal readonly double[] Gr = new double[BandCount];
            internal readonly double[] Rw = new double[BandCount];
            internal readonly double[] Sc = new double[BandCount];
            internal readonly double[] Vg = new double[BandCount];
            internal readonly long[] N = new long[BandCount];
            internal readonly long[] RwN = new long[BandCount];
            internal readonly long[] ScN = new long[BandCount];

            internal readonly double[] EGr, ERw, ESc;
            internal readonly long[] EN, ERwN, EScN;

            internal ShotAcc(string tag, bool rawTwin, bool skyboxLive,
                             double[] stops, bool stopsKnown)
            {
                Tag = tag; RawTwin = rawTwin; SkyboxLive = skyboxLive;
                StopsKnown = stopsKnown;
                if (stops != null)
                    for (int i = 0; i < StopCount && i < stops.Length; i++) Stops[i] = stops[i];
                int b = ElevName.Length;
                EGr = new double[b]; ERw = new double[b]; ESc = new double[b];
                EN = new long[b]; ERwN = new long[b]; EScN = new long[b];
            }

            /// ONE RAY, EVERY NUMERATOR, ONE CALL — `GroundGain.Add`'s rule.
            /// Two tallies fed by two adjacent statements is the shape that
            /// gave this project four pairs of numbers taken at different
            /// instants and printed as one event; with one entry point the
            /// graded, raw and source arms cannot describe different rays
            /// however badly somebody later edits the ray site.
            ///
            /// `rawKnown` is false when the ungraded twin did not render, and
            /// `srcKnown` is false when the ray has no authored value to
            /// divide by — a material with no colour, or a sky ray in a build
            /// whose dome material could not be read. Neither prints as zero;
            /// both print the words, because "the surface renders black" and
            /// "nothing measured it" have different fixes.
            ///
            /// `elevDeg` is used ONLY for `Sky` rays and only for the ladder.
            /// It is passed for every ray anyway so the signature cannot grow
            /// a second overload that a later edit feeds differently.
            public void Add(int band, double gradedLinear,
                            double rawLinear, bool rawKnown,
                            double sourceLinear, bool srcKnown,
                            double vignette, double elevDeg)
            {
                if (band < 0 || band >= BandCount) band = Other;
                Gr[band] += gradedLinear; N[band]++;
                Vg[band] += vignette;
                if (rawKnown) { Rw[band] += rawLinear; RwN[band]++; }
                if (srcKnown) { Sc[band] += sourceLinear; ScN[band]++; }
                if (band != Sky) return;
                int e = ElevOfDegrees(elevDeg);
                EGr[e] += gradedLinear; EN[e]++;
                if (rawKnown) { ERw[e] += rawLinear; ERwN[e]++; }
                if (srcKnown) { ESc[e] += sourceLinear; EScN[e]++; }
            }
        }

        /// OPEN A SHOT, WITH THE REGIME IT IS BEING TAKEN IN AND THE DOME IT
        /// IS BEING TAKEN UNDER.
        ///
        /// `rain` and `wet` are the same two `ValuePanel.Open` takes and go
        /// through the same formatter; `night` is `GameController.NightAmount`
        /// read at the same instant. Pass a NEGATIVE for any of the three when
        /// the caller genuinely does not know — the tag then says so in words.
        /// Never pass zero to mean unknown: zero is a dry noon, which is the
        /// exact regime this instrument exists to isolate.
        ///
        /// `stops` is the dome's six authored numbers IN LINEAR, or null when
        /// the dome could not be read. It is the material's own state, read
        /// back from the live `Material` rather than recomputed from
        /// `LightModel`, so this row describes the sky that was actually in
        /// the frame rather than the sky somebody meant to put there.
        public ShotAcc Open(double rain, double wet, double night,
                            bool rawTwin, bool skyboxLive,
                            double[] stops)
        {
            _shotsOffered++;
            return new ShotAcc(RegimeTag(rain, wet, night), rawTwin, skyboxLive,
                               stops, stops != null);
        }

        /// `<weather>n<night>`, or the WORDS. `ValuePanel.WeatherTag` does the
        /// weather half — ONE implementation, called rather than copied, so a
        /// row here and a row in `valueBands` can be lined up character for
        /// character on the part they share.
        public static string RegimeTag(double rain, double wet, double night)
        {
            string w = ValuePanel.WeatherTag(rain, wet);
            if (night < 0) return w + "nunknown";
            return w + "n" + Num(night, "0.00");
        }

        /// FOLD ONE SHOT INTO ITS REGIME. Every ray this shot cast is added
        /// here, in one statement per band, so a shot that threw mid-loop
        /// contributes nothing rather than a partial row nobody can see the
        /// edge of.
        public void Land(ShotAcc s)
        {
            if (s == null) return;
            _shotsMeasured++;
            if (s.RawTwin) _shotsWithTwin++;
            if (s.SkyboxLive) _shotsSkyboxLive++;
            Reg r;
            if (!_regs.TryGetValue(s.Tag, out r))
            { r = new Reg(s.Tag); _regs[s.Tag] = r; _regSeen.Add(s.Tag); }
            r.Shots++;
            if (s.RawTwin) r.ShotsWithTwin++;
            if (s.SkyboxLive) r.ShotsSkyboxLive++;
            for (int b = 0; b < BandCount; b++)
            {
                r.Gr[b] += s.Gr[b]; r.Rw[b] += s.Rw[b]; r.Sc[b] += s.Sc[b];
                r.Vg[b] += s.Vg[b];
                r.N[b] += s.N[b]; r.RwN[b] += s.RwN[b]; r.ScN[b] += s.ScN[b];
                _rays[b] += s.N[b];
            }
            for (int e = 0; e < ElevName.Length; e++)
            {
                r.EGr[e] += s.EGr[e]; r.ERw[e] += s.ERw[e]; r.ESc[e] += s.ESc[e];
                r.EN[e] += s.EN[e]; r.ERwN[e] += s.ERwN[e]; r.EScN[e] += s.EScN[e];
            }
            if (s.StopsKnown)
            {
                r.StopsSeen = true;
                for (int i = 0; i < StopCount; i++)
                {
                    if (s.Stops[i] < r.StopLo[i]) r.StopLo[i] = s.Stops[i];
                    if (s.Stops[i] > r.StopHi[i]) r.StopHi[i] = s.Stops[i];
                }
            }
        }

        /// THE DOME'S GRADIENT, MIRRORED FROM `LedgerSky.shader` SO THE
        /// AUTHORED SIDE OF THE DIVISION IS THE SHADER'S OWN ARITHMETIC.
        ///
        /// The shader is HLSL and this is C#; they cannot share a body, so
        /// this is the same deliberate mirror `LightModel.VignetteAt` is —
        /// its comment says "mirrors the shader exactly so the test is testing
        /// the shipped arithmetic", and the same words apply here. The two
        /// lines being mirrored are `LedgerSky.shader`'s
        ///
        ///     float up = pow(saturate(h), _SkyCurve);
        ///     float dn = pow(saturate(-h), _GroundCurve);
        ///     c = lerp(_HorizonColor, _SkyColor, up);
        ///     c = lerp(c, _GroundColor, dn);
        ///
        /// and the CURVES ARE NOT RETYPED HERE: the caller reads `_SkyCurve`
        /// and `_GroundCurve` off the live material and passes them, so a
        /// shader tweak cannot leave this mirror describing a dome that is no
        /// longer there.
        ///
        /// LUMA COMMUTES WITH THE LERP AND THAT IS WHY THIS TAKES SCALARS.
        /// Rec.601 luma is a linear combination of the channels and `lerp` is
        /// linear, so `luma(lerp(a,b,t)) == lerp(luma(a),luma(b),t)` exactly
        /// — no approximation, no per-channel array. It is only true because
        /// both sides are in the SAME space, which is the caller's
        /// responsibility and is named at the caller.
        ///
        /// WHAT IT DOES NOT MODEL, said out loud because an unstated omission
        /// in a denominator is the worst kind: THE CLOUD LAYER AND THE SUN
        /// GLOW. Clouds pull the dome toward `_CloudColor` by
        /// `coverage-shaped noise * up * 0.85` and the glow ADDS around the
        /// sun. Both are absent here, so on a ray through cloud or near the
        /// sun the authored value is the CLEAR-SKY one and `xsrc` carries the
        /// difference. That is why `cloud`, `cover` and `glow` are printed on
        /// `skyDomeBy`: they are the size of the omission, and both fade to
        /// nothing at the horizon (`up` and `smoothstep(0,0.10,h)`), so the
        /// low rungs of the ladder — the ones a street camera actually
        /// samples — are the rungs this mirror is exact on.
        public static double DomeLuma(double sinElevation,
                                      double topLinear, double horLinear, double gndLinear,
                                      double skyCurve, double groundCurve)
        {
            double h = sinElevation;
            if (h > 1) h = 1; if (h < -1) h = -1;
            double up = h > 0 ? System.Math.Pow(h, skyCurve) : 0;
            double dn = h < 0 ? System.Math.Pow(-h, groundCurve) : 0;
            double c = horLinear + (topLinear - horLinear) * up;
            return c + (gndLinear - c) * dn;
        }

        /// Which rung of the ladder an elevation falls on. Public so the
        /// test can walk every rung without knowing the edges.
        public static int ElevOfDegrees(double deg)
        {
            if (deg < ElevEdge[0]) return 0;
            for (int i = 1; i < ElevEdge.Length; i++)
                if (deg < ElevEdge[i]) return i;
            return ElevEdge.Length;
        }

        // ---- the done-line rows -------------------------------------------
        //
        // EVERY ONE OF THESE IS A WHOLE-RUN VALUE and belongs on the done
        // line. Nothing here is true of a single shot: the means pool a
        // regime, and a regime is complete only when the run ends. Splitting
        // them onto shot lines would put the same key on twenty lines, which
        // `verdict-read.py` refuses — and would re-open the `nameTagsOffered`
        // fault, where a done-line number and a shot-line number were greped
        // together as one moment.

        /// PER REGIME, PER BAND — the discriminator's own row.
        ///
        /// `<regime>@<band>:gr<graded>/rw<raw>/sc<source>/xgrade<g/r>/xsrc<g/s>@n<rays>/rn<withTwin>/sn<withSource>/vig<mean>`
        ///
        /// REGIMES ARE ORDERED BY ADMITTED RAYS, DESCENDING, and that is a
        /// decision about the CAP rather than about taste: in first-seen order
        /// a run's soaked opening day comes first and the dry noon rows —
        /// which are the whole question — land past row 24 and get truncated.
        /// A cap that can bite the row with the most evidence in it is a cap
        /// that hides the finding. Ties break on the tag, ordinal, so the
        /// order is stable across runs; a regime's four bands stay together.
        ///
        /// `oth` gets no row: a parked car, a body and a sloped roof have no
        /// single authored value to divide by, and pooling them would print a
        /// mean of nothing in particular. They are in `skyGainRays` so the
        /// band counts still add up.
        public string Bands()
        {
            var order = RegimesByRays();
            var rows = new List<string>();
            for (int i = 0; i < order.Count; i++)
            {
                var r = order[i];
                for (int b = 0; b < BandCount; b++)
                {
                    if (b == Other) continue;
                    long n = r.N[b], rn = r.RwN[b], sn = r.ScN[b];
                    string tail = "@n" + n + "/rn" + rn + "/sn" + sn;
                    if (n <= 0)
                    {
                        // RAN AND FOUND NONE. The words, not a zero: a band no
                        // ray landed in — a night frame with no sunlit wall —
                        // and a band rendering at black are different findings
                        // with different fixes.
                        rows.Add(r.Tag + "@" + BandNames[b] + ":nothing_measured" + tail);
                        continue;
                    }
                    double gr = r.Gr[b] / n;
                    double rw = rn > 0 ? r.Rw[b] / rn : 0;
                    double sc = sn > 0 ? r.Sc[b] / sn : 0;
                    rows.Add(r.Tag + "@" + BandNames[b]
                             + ":gr" + Num(gr, "0.0000")
                             + "/rw" + (rn > 0 ? Num(rw, "0.0000") : "none")
                             + "/sc" + (sn > 0 ? Num(sc, "0.0000") : "none")
                             + "/xgrade" + (rn > 0 ? Ratio(gr, rw) : "none")
                             + "/xsrc" + (sn > 0 ? Ratio(gr, sc) : "none")
                             // THE RAW ARM OF THE DIVISION, AND ON THE `sky`
                             // ROW IT IS THE ONE NUMBER WITH AN EXPECTED
                             // VALUE. `rw/sc` has no grade in it at all, so on
                             // the sky it is the dome's own transfer and reads
                             // 1.000 when the dome puts on screen what was
                             // written into it. On the three geometry bands it
                             // is the irradiance and has no expected value —
                             // that asymmetry is the whole discriminator and
                             // is spelled out in the class note above.
                             + "/xrawsrc" + (rn > 0 && sn > 0 ? Ratio(rw, sc) : "none")
                             + tail + "/vig" + Num(r.Vg[b] / n, "0.000"));
                }
            }
            return Rows(rows, RowCap);
        }

        /// THE LADDER — the sky band's rendered-over-authored by ELEVATION,
        /// over ONE regime.
        ///
        /// ONE REGIME, NAMED, because a rung compared across regimes is a
        /// different photograph: the dome's stops move with night and rain, so
        /// the same elevation under two regimes is two different authored
        /// values and the ladder would be measuring the weather. The regime
        /// chosen is the one with the MOST SKY RAYS — a mode, ties broken by
        /// tag ordinal so it is stable — and `skyGainElevOf` names it while
        /// `skyGainElevRegimes` lists every regime that was NOT laddered with
        /// its own sky-ray count, so a reader can see what the choice passed
        /// over instead of having to trust it.
        ///
        /// `<rung>:gr<graded>/rw<raw>/sc<authored>/xgrade<..>/xsrc<..>@n<..>/rn<..>/sn<..>`
        ///
        /// THE RUNG THAT MATTERS IS `xsrc` ON THE **RAW** ARM, and this row
        /// prints the graded ratio because both are wanted; the raw one is
        /// `rw/sc`, which a reader divides on the row. It is the only number
        /// in this file with a KNOWN EXPECTED VALUE — 1.000, the dome putting
        /// on screen what was written into it — and that is what makes the
        /// ladder falsifiable rather than descriptive.
        public string ByElev()
        {
            var r = LadderRegime();
            if (r == null) return "nothing_measured";
            var rows = new List<string>();
            for (int e = 0; e < ElevName.Length; e++)
            {
                long n = r.EN[e], rn = r.ERwN[e], sn = r.EScN[e];
                string tail = "@n" + n + "/rn" + rn + "/sn" + sn;
                if (n <= 0) { rows.Add(ElevName[e] + ":nothing_measured" + tail); continue; }
                double gr = r.EGr[e] / n;
                double rw = rn > 0 ? r.ERw[e] / rn : 0;
                double sc = sn > 0 ? r.ESc[e] / sn : 0;
                rows.Add(ElevName[e]
                         + ":gr" + Num(gr, "0.0000")
                         + "/rw" + (rn > 0 ? Num(rw, "0.0000") : "none")
                         + "/sc" + (sn > 0 ? Num(sc, "0.0000") : "none")
                         + "/xgrade" + (rn > 0 ? Ratio(gr, rw) : "none")
                         + "/xsrc" + (sn > 0 ? Ratio(gr, sc) : "none")
                         + "/xrawsrc" + (rn > 0 && sn > 0 ? Ratio(rw, sc) : "none")
                         + tail);
            }
            return Rows(rows, ElevName.Length);
        }

        /// WHICH REGIME THE LADDER IS OVER, and how many sky rays it stands
        /// on. `nothing_measured` in words when no shot landed a sky ray at
        /// all — a run that photographed no sky and a run whose ladder is
        /// empty must not print alike.
        public string ElevOf()
        {
            var r = LadderRegime();
            if (r == null) return "nothing_measured";
            return r.Tag + "@sky" + r.N[Sky] + "/shots" + r.Shots;
        }

        /// EVERY REGIME'S SKY-RAY COUNT, the same order the bands use — the
        /// denominator for the ladder's choice of one. A regime with more sky
        /// rays than the laddered one cannot exist here by construction; a
        /// regime with nearly as many is a reason to ask for a second ladder.
        public string ElevRegimes()
        {
            var order = RegimesByRays();
            if (order.Count == 0) return "nothing_measured";
            var rows = new List<string>();
            for (int i = 0; i < order.Count; i++)
                rows.Add(order[i].Tag + ":sky" + order[i].N[Sky]
                         + "/all" + order[i].Rays + "/shots" + order[i].Shots);
            return Rows(rows, ListCap);
        }

        /// THE AUTHORED DOME ITSELF, PER REGIME — what the sky's "authored
        /// value" ACTUALLY IS, printed rather than described.
        ///
        /// IT IS NOT A SCALAR AND THIS ROW REFUSES TO PRETEND OTHERWISE. The
        /// dome is a three-stop gradient with a cloud layer and a sun glow
        /// over it, so six numbers are printed and the ladder above is what
        /// turns them into a per-ray denominator. A single "the sky is
        /// authored at X" would be a number invented to make a division
        /// possible.
        ///
        /// EACH STOP PRINTS `lo..hi` WHEN IT MOVED INSIDE THE REGIME AND ONE
        /// NUMBER WHEN IT DID NOT, and that is a self-check rather than a
        /// formatting nicety: `top`, `hor` and `gnd` are deterministic in
        /// (night, rain) and MUST be constant inside a tag, while `cover` is
        /// seeded off the calendar day and must not be. A spread on `top` is
        /// the tag not being the regime it claims to be — suspect this
        /// instrument's tag, not the sky.
        ///
        /// `live<n>/<shots>` is how many of the regime's shots had the
        /// gradient dome actually bound. A build where `Hidden/LedgerSky`
        /// failed to load clears the camera to a flat card and every sky ray
        /// reads one colour at every elevation; that is a completely different
        /// finding from a dark dome and it must not be silent.
        public string DomeBy()
        {
            var order = RegimesByRays();
            var rows = new List<string>();
            for (int i = 0; i < order.Count; i++)
            {
                var r = order[i];
                if (!r.StopsSeen)
                { rows.Add(r.Tag + ":nothing_measured@shots" + r.Shots); continue; }
                var sb = new System.Text.StringBuilder(r.Tag).Append(':');
                for (int k = 0; k < StopCount; k++)
                {
                    if (k > 0) sb.Append('/');
                    sb.Append(StopNames[k]).Append(Span(r.StopLo[k], r.StopHi[k]));
                }
                sb.Append("/live").Append(r.ShotsSkyboxLive).Append('/').Append(r.Shots);
                rows.Add(sb.ToString());
            }
            return Rows(rows, ListCap);
        }

        /// SHOTS MEASURED / OFFERED / WITH-AN-UNGRADED-TWIN / WITH-A-LIVE-DOME.
        ///
        /// `0/0/0/0` is "the instrument never ran"; `0/19/0/0` is "it ran
        /// nineteen times and read nothing back", which is a fault; and
        /// `19/19/0/19` is the one that would otherwise be silent — nineteen
        /// measured shots none of which got an ungraded twin, which makes
        /// every `xgrade` in this key read `none` and makes the whole
        /// discriminator unavailable. They must not print alike (rule 3b).
        public string Shots()
        {
            return _shotsMeasured + "/" + _shotsOffered
                 + "/" + _shotsWithTwin + "/" + _shotsSkyboxLive;
        }

        /// THE BAND RAY COUNTS, cumulative over the run — the denominator for
        /// every mean in `skyGainBands`, and checkable against `valueRays`:
        /// the two instruments are fed from ONE ray loop, so this key's five
        /// counts must equal `valueRays`' five band counts for the shots that
        /// reached this tally. A disagreement is the two classifiers having
        /// drifted apart, which is a fault in the ray site and not in either
        /// number.
        public string Rays()
        {
            long total = 0;
            for (int i = 0; i < BandCount; i++) total += _rays[i];
            return "sky" + _rays[Sky] + "/lit" + _rays[LitWall]
                 + "/gnd" + _rays[Ground] + "/shd" + _rays[Shadow]
                 + "/oth" + _rays[Other] + "/of" + total;
        }

        /// How many rows the capped band list actually shows, over how many
        /// exist — the same shape `refPanelListed` uses.
        public string Listed()
        {
            int total = 0;
            foreach (var kv in _regs) { if (kv.Value != null) total += BandCount - 1; }
            return (total > RowCap ? RowCap : total) + "/" + total;
        }

        // ---- internals -----------------------------------------------------

        /// Regimes ordered by admitted rays DESCENDING, ties by tag ordinal.
        /// Selection-sorted rather than `List.Sort` with a lambda so the
        /// tiebreak is visible in the code that performs it: an arbitrary
        /// winner that changes between runs reads as a world that changed.
        List<Reg> RegimesByRays()
        {
            var all = new List<Reg>();
            for (int i = 0; i < _regSeen.Count; i++)
            {
                Reg r;
                if (_regs.TryGetValue(_regSeen[i], out r) && r != null) all.Add(r);
            }
            var outp = new List<Reg>();
            while (all.Count > 0)
            {
                int best = 0;
                for (int i = 1; i < all.Count; i++)
                {
                    long a = all[i].Rays, b = all[best].Rays;
                    if (a > b || (a == b && string.CompareOrdinal(all[i].Tag, all[best].Tag) < 0))
                        best = i;
                }
                outp.Add(all[best]); all.RemoveAt(best);
            }
            return outp;
        }

        /// The regime with the most SKY rays, or null when no sky ray landed
        /// anywhere. Ties by tag ordinal, for the reason above.
        Reg LadderRegime()
        {
            Reg best = null;
            for (int i = 0; i < _regSeen.Count; i++)
            {
                Reg r;
                if (!_regs.TryGetValue(_regSeen[i], out r) || r == null) continue;
                if (r.N[Sky] <= 0) continue;
                if (best == null || r.N[Sky] > best.N[Sky]
                    || (r.N[Sky] == best.N[Sky] && string.CompareOrdinal(r.Tag, best.Tag) < 0))
                    best = r;
            }
            return best;
        }

        /// `x` when a stop did not move inside its regime, `lo..hi` when it
        /// did. Four decimals: these are linear values and the interesting
        /// ones are small.
        static string Span(double lo, double hi)
        {
            if (lo > hi) return "none";
            if (hi - lo < 5e-5) return Num(lo, "0.0000");
            return Num(lo, "0.0000") + ".." + Num(hi, "0.0000");
        }

        static string Ratio(double num, double den)
        {
            // A source of zero cannot be divided, and printing a large number
            // here would read as an enormous gain. `GroundGain.Ratio`'s word,
            // deliberately the same one, so a grep for the case finds both.
            return den > 1e-9 ? Num(num / den, "0.000") : "source0";
        }

        static string Rows(List<string> rows, int cap)
        {
            if (rows == null || rows.Count == 0) return "nothing_measured";
            var sb = new System.Text.StringBuilder("[");
            int n = rows.Count < cap ? rows.Count : cap;
            for (int i = 0; i < n; i++)
            {
                if (i > 0) sb.Append(',');
                sb.Append(rows[i]);
            }
            // THE CAP ANNOUNCES ITSELF, inside the bracket so the whole value
            // stays one whitespace-free token. A truncation that does not say
            // it bit reads as a finding.
            if (rows.Count > cap)
                sb.Append(",+").Append(rows.Count - cap).Append("more-not-shown");
            return sb.Append(']').ToString();
        }

        /// INVARIANT CULTURE. A comma-decimal runner would emit `0,417` and
        /// every reader would take `0` and drop the rest — the silent
        /// truncation the no-spaces rule exists for, one character further in.
        static string Num(double v, string fmt)
        {
            return v.ToString(fmt, CultureInfo.InvariantCulture);
        }
    }
}
