using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// Constructs the city block at runtime from primitives, dressed with materials
    /// from AssetLibrary (procedural now, a purchased pack later without code change).
    /// Still a graybox in silhouette — the goal here is that surfaces read as asphalt,
    /// brick, and concrete rather than flat-shaded cubes, and that the street has real
    /// sidewalks and kerbs.
    public static class WorldBuilder
    {
        public static readonly Vector3 BarDoor = new Vector3(-6, 0, 6);
        public static readonly Vector3 BarCounter = new Vector3(-8.5f, 0, 8.5f);

        static readonly List<Light> Lamps = new List<Light>();
        static readonly List<Renderer> Windows = new List<Renderer>();
        /// Whether each window is a ground-floor SHOPFRONT, in step with
        /// `Windows`.
        ///
        /// A PARALLEL LIST RATHER THAN PARSING THE NAME BACK OUT. The names do
        /// encode the floor — `..._win_xP_0_0` — and reading it back would work
        /// today and break the first time somebody renames a window, silently,
        /// by making every shopfront a flat again. The build already knows
        /// which is which; the honest thing is to keep the answer rather than
        /// re-derive it from a string.
        static readonly List<bool> WindowIsShop = new List<bool>();
        /// Per-window glow strength, filled beside the other two lists in
        /// `AddWindow` and read by the lit sweep. Small windows burn at full
        /// strength; a band wider than a room gets a hashed dimming so a
        /// far wall reads as a patchwork of different rooms instead of one
        /// glowing sheet — the wall-of-light fix that survived the emission
        /// mask's death, because it rides the COLOUR, which provably works.
        static readonly List<float> WindowGlowScale = new List<float>();
        /// Warm interior glow, HDR emission.
        ///
        /// A SUSPECT, NOT A VERDICT, and it is written down so nobody — me
        /// included — changes it on a hunch. In `review_day1_night.jpg` whole
        /// floors read as solid blown-white slabs rather than as lit rooms, and
        /// the 3.0 multiplier is the obvious candidate: it puts red at 3.0,
        /// which clips hard after the tonemap and then blooms.
        ///
        /// OBVIOUS IS NOT MEASURED. Three times in one night this project
        /// condemned correct work from a still — three textures the noir tint
        /// had already neutralised, a bench, a set of wheels within a few
        /// percent of a real car — so the rule is that a visual judgement is a
        /// HYPOTHESIS until a number answers it.
        ///
        /// THE COLOUR IS LOST IN THE POST CHAIN, NOT HERE. Settled, parked.
        ///
        /// Three versions of one probe to establish it, each measuring something
        /// real and reporting it as the answer to a different question:
        ///
        ///   all bright pixels    b/r 0.82 at k=1.0 — mostly lamps and neon
        ///   lit minus dark       b/r 0.70 at k=1.0 — source plus wall spill
        ///   the top decile       b/r 0.72 at k=1.0 — the window faces alone
        ///
        /// At k=1.0 there is no multiplier, nothing clips, and the window
        /// rectangles STILL come out at 0.72 against a target of 0.45. Every
        /// hypothesis about this constant is dead: it is not the multiplier, it
        /// is not clipping, and it is not the window geometry.
        ///
        /// What is left is the post chain. ACES desaturates hard at the top of
        /// its curve, which is exactly where a lit window sits, and bloom then
        /// spreads a near-white halo over the result. Both are working as
        /// designed and both are global.
        ///
        /// PARKED, AND NOW UNPARKED WITH ONE MEASUREMENT RATHER THAN FOUR
        /// BUILDS. The note here said the options were to pre-compensate the
        /// colour, soften bloom on emissives, or accept it — "all three
        /// art-direction calls on a global grade", each costing a round trip.
        /// The first is now a SWEEP: `windowWarmth` renders the same frame at
        /// six source blues and prints what each produces, so the colour that
        /// lands on target is read off a line instead of guessed and defended.
        /// One build, and the decision takes a minute.
        ///
        /// The constant has never moved. That is the point: three confident
        /// diagnoses, none of them right, and none of them cost a commit.
        ///
        /// ONE COLOUR, AND FOR TWO HOURS TONIGHT THERE WERE TWO. Adding
        /// `WindowEmissive` for the probe to sweep left this line holding its
        /// own private copy of the same three numbers — so the sweep would have
        /// measured one colour while the shipped windows used another, and the
        /// answer it produced could not have been applied by changing the thing
        /// it measured. A probe whose result cannot be acted on is worse than
        /// no probe: it looks like progress.
        ///
        /// `CityPlan` exists because of exactly this ("nothing may hold a
        /// second copy"), and I made a second copy of a constant in the middle
        /// of a night spent finding other people's. Derived now, so they cannot
        /// disagree.
        /// A PROPERTY, NOT A FIELD, and both reasons matter.
        ///
        /// Static field initialisers run in DECLARATION ORDER, and
        /// `WindowEmissive` is declared below this — so `static readonly Color
        /// WindowLit = WindowEmissive * ...` would have read an uninitialised
        /// colour and lit every window in the city black. Nothing local catches
        /// that: it compiles, and `ShapeCheck` is reference-independent.
        ///
        /// And `readonly` would have frozen the value at load, so the sweep
        /// could change `WindowEmissive` and the windows would not follow —
        /// which is the same "the answer cannot be applied" fault one level
        /// down from the one this whole change exists to fix.
        static Color WindowLit => WindowEmissive * WindowGlowMultiplier;

        /// The multiplier under test, so the probe can sweep it without this
        /// file and the sim disagreeing about what was rendered.
        /// THE COLOUR A LIT WINDOW EMITS, before anything renders it.
        ///
        /// Named rather than inline because the probe now sweeps it. The night
        /// still shows windows as white slabs, and the six-multiplier series
        /// says brightness is not the reason: the measured blue-over-red runs
        /// 0.71 to 0.79 across a 3x range and RISES with the multiplier, while
        /// the target is 0.45. There is no multiplier that reaches it, so the
        /// probe's own instruction — "ship the largest k whose blue ratio is
        /// still near 0.45" — was unsatisfiable, and had been for as long as it
        /// has been printed.
        ///
        /// The source is already 0.45. Everything between here and the frame —
        /// bloom spreading a near-white halo, ACES desaturating highlights —
        /// pulls it toward white. So the number to find is not a brightness,
        /// it is the source colour that COMES OUT at 0.45, and that is a
        /// transfer to be measured rather than reasoned about.
        /// READ OFF THE SERIES, not chosen. `[series] windowWarmth` at 6b64b40,
        /// sweeping the source blue at a fixed multiplier and measuring what
        /// the FRAME comes out at:
        ///
        ///     src 0.45 -> b/r 0.83      src 0.14 -> b/r 0.41
        ///     src 0.32 -> b/r 0.72      src 0.06 -> b/r 0.17
        ///     src 0.22 -> b/r 0.59      src 0.00 -> b/r 0.00
        ///
        /// Nearly linear at about 1.85x, and the target of 0.45 on screen sits
        /// between the 0.14 and 0.22 samples: 0.16. That is the number three
        /// confident diagnoses failed to reach, and it took one build once the
        /// sweep was on the right axis — the multiplier had been swept six ways
        /// and never moved b/r below 0.68 because brightness was never the
        /// lever.
        ///
        /// AND THE BLUE ANSWER CAME BACK EXACTLY AS THE SERIES PREDICTED,
        /// which is the part worth recording. The line said 0.16 would land on
        /// 0.45; the next build measured `b/r=0.43`. Read off, shipped,
        /// confirmed — after three confident diagnoses had failed on the same
        /// question because they were all sweeping brightness, which was never
        /// the lever.
        ///
        /// GREEN, THE SAME WAY. Swept at the shipped blue so the two do not
        /// confound:
        ///
        ///     srcG 0.82 -> g/r 0.97      srcG 0.46 -> g/r 0.80
        ///     srcG 0.70 -> g/r 0.93      srcG 0.34 -> g/r 0.69
        ///     srcG 0.58 -> g/r 0.88      srcG 0.20 -> g/r 0.47
        ///
        /// The 0.82 target sits between the 0.46 and 0.58 samples: 0.49.
        ///
        /// So the source is (1.00, 0.49, 0.16) and it looks violently orange
        /// as a raw colour — which is the whole point. ACES desaturates the
        /// top of its curve and bloom spreads a near-white halo, and
        /// pre-compensating for both is what puts (1.00, 0.82, 0.45) on the
        /// screen. The number that matters is the one in the frame.
        public static Color WindowEmissive = new Color(1.0f, 0.49f, 0.16f);

        /// How much brighter than the source a lit window renders. Named
        /// because `WindowLit` is built from it and the probe sweeps around
        /// it; the six-point series that chose 3.0 is above.
        ///
        /// 3.0 → 1.8 for LINEAR (M17.10 V1.5): the whole six-point series
        /// above was swept in gamma, where the display lifted every emissive
        /// mid-tone. The flip's A/B put the night scene mean at 0.255
        /// against noon's 0.172 — night brighter than day — and the first
        /// linear night still shows every window blooming a halo. The
        /// aperture cannot take the excess (its tested floor refused, see
        /// Exposure); the source is the honest knob, cut by roughly the
        /// measured overshoot. Round two: 1.8 read night 0.241 against day
        /// 0.195 — still inverted on 7 of 10 days — so another step down;
        /// the night still at 1.8 already reads as lamps, not floodlights,
        /// and the halo margin is there to spend.
        ///
        /// Round three REVERSES half of round two: cutting 1.8 -> 1.4 moved
        /// the night scene mean not at all (0.241 -> 0.242) — the windows
        /// are small by AREA and the mean lives in the fog, which round
        /// three converts at its own site. What the cut DID buy was a
        /// flatter, less atmospheric night still. Back up to 1.7: inside
        /// the measured do-no-harm band, chosen for the halo.
        public const float WindowGlowMultiplier = 1.7f;

        public static void SetWindowGlow(float multiplier)
        {
            var c = WindowEmissive * multiplier;
            foreach (var r in Windows)
            {
                if (r == null) continue;
                var mpb = new MaterialPropertyBlock();
                r.GetPropertyBlock(mpb);
                mpb.SetColor("_EmissionColor", c);
                r.SetPropertyBlock(mpb);
            }
        }
        static readonly Color WindowDark = new Color(0.02f, 0.02f, 0.02f);
        static bool _windowsLit;

        /// Hide every window renderer for one probe render, restoring the
        /// EXACT prior state after — snapshot rather than blanket re-enable,
        /// so a renderer some other system disabled stays disabled. For the
        /// noonFacade ladder's winOff rung: day glass is authored near-black
        /// (Window tint ~0.01 linear), and whether the dark left third is
        /// the GLASS or the WALL decides which fix is next.
        static bool[] _winWasEnabled;
        public static void HideWindowsForCapture()
        {
            _winWasEnabled = new bool[Windows.Count];
            for (int i = 0; i < Windows.Count; i++)
            {
                var r = Windows[i];
                if (r == null) continue;
                _winWasEnabled[i] = r.enabled;
                r.enabled = false;
            }
        }
        public static void RestoreWindowsAfterCapture()
        {
            if (_winWasEnabled == null) return;
            for (int i = 0; i < Windows.Count && i < _winWasEnabled.Length; i++)
            {
                var r = Windows[i];
                if (r != null) r.enabled = _winWasEnabled[i];
            }
            _winWasEnabled = null;
        }

        public static void BuildBlock()
        {
            Lamps.Clear();
            Windows.Clear();
            FireEscapes = 0;
            Mullions = 0;
            // Per BUILD, like every counter beside it — a static that
            // survives a rebuild reports the sum of two towns.
            SillCount = 0;
            WindowIsShop.Clear();
            WindowGlowScale.Clear();
            Masses.Clear();
            PrimaryMasses.Clear();
            Masses.AddRange(BuildBlockSpecs());
            _windowsLit = false;
            WindowPanes = 0; WindowBands = 0;
            Doors = 0;
            DoorHost.Reset();
            AssetLibrary.ResetPaint();
            System.Array.Clear(PremisesBuilt, 0, PremisesBuilt.Length);
            PremisesByDistrict.Clear();
            AssetLibrary.Initialize();
            ConfigureEnvironment();

            // Ground slab — sized for the district, not just the founding street.
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground";
            // Sized from the MAP, not from a remembered pair of districts: M14
            // added four more and five of the seven were standing on nothing,
            // which is what "the streets glitch" looks like from inside — road
            // slabs floating over the skybox (playtest, 2026-07-28).
            double gMinX = double.MaxValue, gMaxX = double.MinValue;
            double gMinZ = double.MaxValue, gMaxZ = double.MinValue;
            foreach (var d in Ledger.Core.StreetMap.Districts)
            {
                // SCALED, AND THE COMMENT ABOVE IS ABOUT THIS EXACT SYMPTOM.
                //
                // "Five of the seven were standing on nothing — road slabs
                // floating over the skybox" was diagnosed in July as the ground
                // plane not following the districts, and the fix made it follow
                // the AVENUE ARRAYS. Those are unscaled source data: the ground
                // was sized -200..160 while the blocks reach -426..340, so the
                // outer districts have been standing off the edge of it ever
                // since. The right symptom, the right instinct, and a raw read
                // of the one array in this codebase that must never be read raw.
                Ledger.Core.StreetMap.BoundsOf(d, out var dx0, out var dx1,
                                               out var dz0, out var dz1);
                gMinX = System.Math.Min(gMinX, dx0);
                gMaxX = System.Math.Max(gMaxX, dx1);
                gMinZ = System.Math.Min(gMinZ, dz0);
                gMaxZ = System.Math.Max(gMaxZ, dz1);
            }
            const float shoulder = 40f;   // you can walk past the last junction
            float gw = (float)(gMaxX - gMinX) + shoulder * 2f;
            float gd = (float)(gMaxZ - gMinZ) + shoulder * 2f;
            ground.transform.position = new Vector3(
                (float)(gMinX + gMaxX) / 2f, 0, (float)(gMinZ + gMaxZ) / 2f);
            // A Unity Plane is 10m per unit of scale.
            ground.transform.localScale = new Vector3(gw / 10f, 1, gd / 10f);
            ground.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Concrete);
            SetTiling(ground, Mathf.RoundToInt(gw / 3f), Mathf.RoundToInt(gd / 3f));

            BuildStreetsAndWalks();
            BuildBuildings();
            BuildBar();
            BuildProps();
            BuildLamps();
            BuildNeon();
            BuildDistrict();
            BuildLandmarks();
            BuildSkyline();
            // Signs last: they read the finished network, and a rule the city
            // obeys without telling you is indistinguishable from a bug.
            StreetFurniture.Build();
            // And the parked cars after even the signs: they append to
            // `Masses`, and everything that reads Masses as BUILDING specs
            // (BuildBuildings, the name-plate wall finder) has run by now —
            // from here on the list is only consulted as obstacles.
            BuildParkedCars();
            BuildSmoke();
            BuildGulls();
            // LAST, so it sees the finished world: anything still wearing
            // Unity's default white is something nobody dressed.
            AuditUndressed();
        }

        /// Built-in-pipeline environment: gradient ambient + distance fog. The per-frame
        /// colours are driven by GameController.UpdateSun; these are the static defaults.
        /// NEON (art pass 2026-07-28). The single strongest argument that a
        /// rain-soaked 1990 street is INVITING rather than bleak: saturated
        /// coloured light, pooling on wet asphalt, marking the places that are
        /// open when everything else is shut. Deliberately concentrated on the
        /// Strip and on the bar — the two places the game wants you to walk
        /// toward — so the colour is doing navigational work as well as mood.
        static readonly (string place, Color colour, string word)[] NeonSigns =
        {
            ("marquee_club",    new Color(1.00f, 0.15f, 0.55f), "MARQUEE"),
            ("card_rooms",      new Color(0.20f, 0.85f, 1.00f), "CARDS"),
            ("allnight_counter",new Color(1.00f, 0.65f, 0.10f), "OPEN ALL NITE"),
            ("strip_boarding",  new Color(0.45f, 0.35f, 1.00f), "ROOMS"),
            ("bar_door",        new Color(1.00f, 0.35f, 0.12f), "MICKEY'S"),
            ("bathhouse",       new Color(0.30f, 1.00f, 0.70f), "BATHS"),
            ("gull_boarding",   new Color(1.00f, 0.75f, 0.25f), "VACANCY"),
            ("covered_market",  new Color(0.95f, 0.90f, 0.35f), "MARKET"),
        };

        static void BuildNeon()
        {
            foreach (var (placeId, colour, word) in NeonSigns)
            {
                var place = Ledger.Core.HookMap.Get(placeId);
                if (place == null) continue;
                var at = new Vector3((float)place.X, 3.4f, (float)place.Z);

                // The sign itself: a small emissive panel that reads as a
                // light source even before its lamp is counted.
                var panel = GameObject.CreatePrimitive(PrimitiveType.Cube);
                panel.name = $"Neon_{placeId}";
                panel.transform.position = at;
                panel.transform.localScale = new Vector3(2.6f, 0.55f, 0.12f);
                var mat = new Material(Shader.Find("Standard"));
                mat.color = colour * 0.35f;
                mat.EnableKeyword("_EMISSION");
                // SCALE TO THE BRIGHTEST CHANNEL, never multiply uniformly.
                // `colour * 2.2` was the first attempt and it clipped every
                // channel above 0.45 to white, so ROOMS, BATHS, VACANCY and
                // MARKET all rendered as bright grey — half the signs, and
                // the pale ones that carry the warmth. The CI render
                // fingerprint caught it: bright pixels averaging 247,249,244
                // on a night frame that is meant to be full of colour.
                var (er, eg, eb) = Ledger.Core.Palette.Emissive(
                    colour.r, colour.g, colour.b, 0.95);
                mat.SetColor("_EmissionColor", new Color((float)er, (float)eg, (float)eb));
                panel.GetComponent<Renderer>().sharedMaterial = mat;
                Object.Destroy(panel.GetComponent<Collider>());

                // And the pool it throws. This is the part that lands on wet
                // asphalt and does the actual work.
                var lampGo = new GameObject($"NeonLight_{placeId}");
                lampGo.transform.position = at + Vector3.down * 0.4f;
                var light = lampGo.AddComponent<Light>();
                light.type = LightType.Point;
                light.color = colour;
                light.range = 13f;
                // The panel is no longer allowed to blow out, so the APPARENT
                // brightness has to come from the pool it throws instead —
                // which is the more truthful model anyway. A neon tube is not
                // very bright; it just looks it against a dark wet street,
                // and the light on the asphalt is what the eye actually reads.
                // 2.9 → 2.1 for LINEAR (V1.5 round four): point lights
                // render hotter in linear, and the landed night still
                // measured a floor of 0.15 luma across its darkest tenth —
                // a night with no darks, held up by overlapping light
                // pools. One consistent ~0.7x trim across lamps, neon and
                // kerb lights keeps their ratios; "the lamps do the
                // lifting" survives, just in honest units.
                light.intensity = 2.1f;
                // Neon throws a shorter, brighter shaft than a street lamp —
                // a tube is a small source and its cone is tight.
                LightShaft.Attach(light, 0.7f);
                _neon.Add(light);
            }
        }

        static readonly System.Collections.Generic.List<Light> _neon =
            new System.Collections.Generic.List<Light>();

        /// Neon is a night thing, and it flickers a little because a sign in
        /// 1990 that never flickered was a sign somebody was maintaining.
        /// BY DAY THIS IS A SWEEP THAT SETS THE SAME FALSE OVER AND OVER.
        /// The night pass has to run every frame — it drives the flicker —
        /// but the daytime pass only turns everything off, which stays off.
        /// Same count guard as the lamps, and for the same reason: a neon
        /// sign built after the last sweep still has to be dealt with.
        public static void TickNeon(bool night, float time)
        {
            if (!night)
            {
                // Done already, and no sign has been built since.
                if (_neonDayDoneAt == _neon.Count) { NeonSweepsSkipped++; return; }
                _neonDayDoneAt = _neon.Count;
            }
            else _neonDayDoneAt = -1;    // night sweeps every frame; re-arm the day guard
            NeonSweeps++;

            for (int i = 0; i < _neon.Count; i++)
            {
                var l = _neon[i];
                if (l == null) continue;
                if (!night) { l.enabled = false; continue; }
                l.enabled = true;
                float flicker = 1f + 0.06f * Mathf.Sin(time * (3.1f + i * 0.7f))
                                   + (i % 4 == 0 && Mathf.PerlinNoise(time * 2.3f, i) > 0.93f ? -0.5f : 0f);
                l.intensity = 2.1f * flicker;
            }
        }

        static void ConfigureEnvironment()
        {
            // SceneLighting owns ambient, fog and shadows now, and drives all
            // three per frame off LightModel. The fixed linear fog that used
            // to live here was a second authority on the same settings — it
            // never changed with the hour, so night fog was the same grey as
            // noon fog, which is the single most common way a street reads as
            // untextured game rather than photograph.
            SceneLighting.Ensure();
        }

        /// Roads, built from the network in Core rather than from two hardcoded
        /// axes. Every driveable edge becomes tarmac with a centre line, every
        /// junction gets a pad, and every block gets pavement and kerb around
        /// its four sides — with the corners chamfered, which is Barcelona's
        /// trick and the cheapest thing that stops a grid reading as graph paper.
        static void BuildStreetsAndWalks()
        {
            ZebraSpots.Clear();
            var map = Ledger.Core.StreetMap.Edges;

            // 1. Tarmac along every road. Lanes are paved too but narrower and
            // without markings — they are driveways, not streets.
            int n = 0;
            foreach (var e in map)
            {
                var a = Ledger.Core.StreetMap.Node(e.A);
                var b = Ledger.Core.StreetMap.Node(e.B);
                var pa = new Vector3((float)a.X, 0, (float)a.Z);
                var pb = new Vector3((float)b.X, 0, (float)b.Z);
                var mid = (pa + pb) * 0.5f;
                var span = pb - pa;
                float len = span.magnitude;
                if (len < 0.5f) continue;

                bool alongZ = Mathf.Abs(span.z) > Mathf.Abs(span.x);
                float w = (float)e.Width;
                var size = alongZ ? new Vector3(w, 0.04f, len) : new Vector3(len, 0.04f, w);
                var road = MakeBox($"Road_{n}", mid + new Vector3(0, 0.02f, 0), size,
                    e.Driveable ? AssetLibrary.Asphalt : AssetLibrary.Concrete);
                SetTiling(road, alongZ ? 3 : Mathf.RoundToInt(len / 2f),
                                alongZ ? Mathf.RoundToInt(len / 2f) : 3);

                // A dashed centre line, so a road reads as a road at a glance.
                if (e.Driveable && len > 12f)
                {
                    int dashes = Mathf.FloorToInt(len / 6f);
                    for (int d = 0; d < dashes; d++)
                    {
                        float t = (d + 0.5f) / dashes;
                        var at = Vector3.Lerp(pa, pb, t) + new Vector3(0, 0.05f, 0);
                        MakeBox($"Line_{n}_{d}", at,
                            alongZ ? new Vector3(0.22f, 0.02f, 2.4f) : new Vector3(2.4f, 0.02f, 0.22f),
                            AssetLibrary.Sidewalk);
                    }
                }

                // SINGLE yellow lines along the kerbs of the commercial
                // spines (town-plan T2) — "a council manages this street" in
                // one stroke of paint. Single and not double on purpose: the
                // kerbs carry parked cars, and to a British eye a car on a
                // DOUBLE yellow is a mistake in the world's grammar, while
                // eighties parking on a single yellow is just the afternoon.
                if (TownPlanEnabled && e.Driveable && e.Kind != "lane" && len > 14f
                    && Ledger.Core.Dressing.NearestCore(mid.x, mid.z, DenseCores) <= NearCoreMetres)
                {
                    foreach (var s in new[] { 1f, -1f })
                    {
                        var ypos = mid + (alongZ ? new Vector3(s * (w / 2f - 0.5f), 0.045f, 0)
                                                 : new Vector3(0, 0.045f, s * (w / 2f - 0.5f)));
                        Tint(MakeBox($"Yellow_{n}_{(s > 0 ? "p" : "m")}", ypos,
                            alongZ ? new Vector3(0.09f, 0.015f, len - 10f)
                                   : new Vector3(len - 10f, 0.015f, 0.09f),
                            AssetLibrary.Sidewalk), new Color(0.62f, 0.52f, 0.18f));
                    }

                    // A ZEBRA on roughly every third core street, off-centre so
                    // it reads as placed for people rather than for symmetry,
                    // with a belisha beacon on each kerb — the single most
                    // British object a road can carry, and the players WILL
                    // cross these roads. Stripes run with the traffic, as real
                    // ones do; the spot is recorded so the parked cars keep
                    // clear (a car on a zebra is worse grammar than no zebra).
                    if (len > 24f && (StableHash(e.A) + StableHash(e.B)) % 3 == 0)
                    {
                        var zc = Vector3.Lerp(pa, pb, 0.38f);
                        ZebraSpots.Add(zc);
                        var dirAlong = (pb - pa).normalized;
                        var across = new Vector3(-dirAlong.z, 0, dirAlong.x);
                        int stripes = Mathf.FloorToInt((w - 1.2f) / 1.0f);
                        for (int zi = 0; zi < stripes; zi++)
                        {
                            float off = -(w - 1.2f) / 2f + 0.5f + zi * 1.0f;
                            var sp = zc + across * off + new Vector3(0, 0.055f, 0);
                            var stripe = MakeBox($"Zebra_{n}_{zi}", sp,
                                new Vector3(0.5f, 0.015f, 2.6f), AssetLibrary.Sidewalk);
                            stripe.transform.rotation = Quaternion.LookRotation(dirAlong);
                            Tint(stripe, new Color(0.85f, 0.86f, 0.84f));
                        }
                        foreach (var bs in new[] { 1f, -1f })
                        {
                            var bpos = zc + across * bs * (w / 2f + 0.6f);
                            MakeBox($"Belisha_{n}_{(bs > 0 ? "p" : "m")}_pole",
                                bpos + new Vector3(0, 1.25f, 0),
                                new Vector3(0.09f, 2.5f, 0.09f), AssetLibrary.Metal);
                            var ball = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                            ball.name = $"Belisha_{n}_{(bs > 0 ? "p" : "m")}_ball";
                            ball.transform.position = bpos + new Vector3(0, 2.65f, 0);
                            ball.transform.localScale = Vector3.one * 0.32f;
                            ball.GetComponent<Renderer>().sharedMaterial =
                                AssetLibrary.Material(AssetLibrary.Plaster);
                            Tint(ball, new Color(0.95f, 0.62f, 0.12f));
                            Object.Destroy(ball.GetComponent<Collider>());
                        }
                    }
                }
                n++;
            }

            // 2. Junction pads, so crossings do not show a seam where two
            // strips of tarmac meet at right angles.
            foreach (var j in Ledger.Core.StreetMap.Nodes)
            {
                if (!j.IsJunction) continue;
                float w = (float)Ledger.Core.StreetMap.AvenueWidth;
                MakeBox($"Junction_{j.Id}", new Vector3((float)j.X, 0.025f, (float)j.Z),
                    new Vector3(w, 0.04f, w), AssetLibrary.Asphalt);
            }

            // 3. Pavement and kerb around every block. Under TownPlanEnabled the
            // corners are SQUARE and the kerb closes through them; the legacy
            // path below it keeps the chamfered plate-island look for the
            // Tuesday-noon revert.
            int bi = 0;
            foreach (var b in Ledger.Core.StreetMap.Blocks)
            {
                float cx = (float)b.CentreX, cz = (float)b.CentreZ;
                float hw = (float)b.Width / 2f, hd = (float)b.Depth / 2f;
                float ch = (float)Ledger.Core.StreetMap.Chamfer;
                const float walk = 2.2f, kerbH = 0.34f;

                if (TownPlanEnabled)
                {
                    // TOWN-PLAN.MD T1 item 2: the ribbon. Z strips own the full
                    // width including both corners; X strips are shortened by one
                    // pavement width at each end so the pair ABUT rather than
                    // overlap — two coplanar tops in the same square would
                    // z-fight. Square corners, no pads, nothing rotated.
                    MakeBox($"Walk_{bi}_zP", new Vector3(cx, 0.16f, cz + hd - walk / 2f),
                        new Vector3((float)b.Width, 0.32f, walk), AssetLibrary.Sidewalk);
                    MakeBox($"Walk_{bi}_zN", new Vector3(cx, 0.16f, cz - hd + walk / 2f),
                        new Vector3((float)b.Width, 0.32f, walk), AssetLibrary.Sidewalk);
                    float xLen = b.Depth > 2 * walk ? (float)b.Depth - 2 * walk : 1f;
                    MakeBox($"Walk_{bi}_xP", new Vector3(cx + hw - walk / 2f, 0.16f, cz),
                        new Vector3(walk, 0.32f, xLen), AssetLibrary.Sidewalk);
                    MakeBox($"Walk_{bi}_xN", new Vector3(cx - hw + walk / 2f, 0.16f, cz),
                        new Vector3(walk, 0.32f, xLen), AssetLibrary.Sidewalk);

                    // Kerb runs unbroken to the corner: the Z pair carries 0.2
                    // past each end to close the notch where the two runs meet.
                    MakeBox($"Kerb_{bi}_zP", new Vector3(cx, 0.20f, cz + hd + 0.1f),
                        new Vector3((float)b.Width + 0.4f, kerbH, 0.2f), AssetLibrary.Kerb);
                    MakeBox($"Kerb_{bi}_zN", new Vector3(cx, 0.20f, cz - hd - 0.1f),
                        new Vector3((float)b.Width + 0.4f, kerbH, 0.2f), AssetLibrary.Kerb);
                    MakeBox($"Kerb_{bi}_xP", new Vector3(cx + hw + 0.1f, 0.20f, cz),
                        new Vector3(0.2f, kerbH, (float)b.Depth), AssetLibrary.Kerb);
                    MakeBox($"Kerb_{bi}_xN", new Vector3(cx - hw - 0.1f, 0.20f, cz),
                        new Vector3(0.2f, kerbH, (float)b.Depth), AssetLibrary.Kerb);
                    bi++;
                    continue;
                }

                // Four pavement strips, each shortened by the chamfer so the
                // corners are cut rather than square.
                MakeBox($"Walk_{bi}_zP", new Vector3(cx, 0.16f, cz + hd - walk / 2f),
                    new Vector3(b.Width > 2 * ch ? (float)b.Width - 2 * ch : 1f, 0.32f, walk), AssetLibrary.Sidewalk);
                MakeBox($"Walk_{bi}_zN", new Vector3(cx, 0.16f, cz - hd + walk / 2f),
                    new Vector3(b.Width > 2 * ch ? (float)b.Width - 2 * ch : 1f, 0.32f, walk), AssetLibrary.Sidewalk);
                MakeBox($"Walk_{bi}_xP", new Vector3(cx + hw - walk / 2f, 0.16f, cz),
                    new Vector3(walk, 0.32f, b.Depth > 2 * ch ? (float)b.Depth - 2 * ch : 1f), AssetLibrary.Sidewalk);
                MakeBox($"Walk_{bi}_xN", new Vector3(cx - hw + walk / 2f, 0.16f, cz),
                    new Vector3(walk, 0.32f, b.Depth > 2 * ch ? (float)b.Depth - 2 * ch : 1f), AssetLibrary.Sidewalk);

                // The chamfer itself: a small pad across each cut corner, turning
                // every crossroads into a little plaza.
                foreach (var sx in new[] { 1f, -1f })
                    foreach (var sz in new[] { 1f, -1f })
                    {
                        var corner = new Vector3(cx + sx * (hw - ch / 2f), 0.16f, cz + sz * (hd - ch / 2f));
                        var pad = MakeBox($"Chamfer_{bi}_{sx}_{sz}", corner,
                            new Vector3(ch * 1.45f, 0.32f, ch * 1.45f), AssetLibrary.Sidewalk);
                        pad.transform.rotation = Quaternion.Euler(0, 45, 0);
                    }

                // Kerbs, just outside the pavement on each side.
                MakeBox($"Kerb_{bi}_zP", new Vector3(cx, 0.20f, cz + hd + 0.1f),
                    new Vector3((float)b.Width - 2 * ch, kerbH, 0.2f), AssetLibrary.Kerb);
                MakeBox($"Kerb_{bi}_zN", new Vector3(cx, 0.20f, cz - hd - 0.1f),
                    new Vector3((float)b.Width - 2 * ch, kerbH, 0.2f), AssetLibrary.Kerb);
                MakeBox($"Kerb_{bi}_xP", new Vector3(cx + hw + 0.1f, 0.20f, cz),
                    new Vector3(0.2f, kerbH, (float)b.Depth - 2 * ch), AssetLibrary.Kerb);
                MakeBox($"Kerb_{bi}_xN", new Vector3(cx - hw - 0.1f, 0.20f, cz),
                    new Vector3(0.2f, kerbH, (float)b.Depth - 2 * ch), AssetLibrary.Kerb);
                bi++;
            }
        }

        /// XZ solid masses of the block. NpcWalker consults these to route around
        /// buildings instead of through them; kept as data so the routing needs no
        /// physics casts (deterministic under the accelerated sim). The founding
        /// street's specs are fixed; the district build-out appends its own.
        /// Buildings are no longer hand-placed. They are GENERATED TO FILL THE
        /// BLOCKS, which is the only arrangement that survives having real
        /// streets: three of the seven original boxes stood exactly where an
        /// avenue needed to go. Each block gets a terrace of two to four
        /// buildings of varied footprint and height, set back from the kerb,
        /// with the bar's block and every named place left clear.
        ///
        /// Deterministic from the block index, so the city is the same city
        /// every run and the CI screenshots stay comparable.
        /// TOWN-PLAN.MD T1, the switch. One constant, so Tuesday-noon's
        /// decision is a one-line revert with the old arrangement code
        /// standing untouched beside the new.
        public const bool TownPlanEnabled = true;

        /// Chimney stacks recorded by the terrace generator (one per party
        /// wall, on the roofline) and built after the buildings are — the
        /// generator makes SPECS, geometry belongs to the build pass, and a
        /// chimney needs to know its parcel's height which only the spec
        /// moment knows.
        static readonly List<(Vector3 pos, float baseY)> TerraceChimneys
            = new List<(Vector3, float)>();

        /// INSTRUMENTS for the smoke mystery (16 Aug): smokeStacks came back
        /// 2 when the arithmetic said ~35, no stack shows on any roofline,
        /// and every line of the recording, emission and smoke code reads
        /// correct — so one of the assumptions underneath them is wrong and
        /// no amount of rereading will say which. Four counters, printed on
        /// the done line, pin the stage: how many blocks took each massing
        /// path, how many parcels the terraces added, how many chimneys
        /// were recorded. One build answers what an afternoon of armchair
        /// deduction could not.
        public static int TerracedBlocks, LegacyBlocks, TerraceParcels;
        /// Parcels per district. See the note at the increment site: a
        /// pixel statistic over the district frames could not tell a built
        /// street from an empty field, so the builder counts instead.
        public static readonly System.Collections.Generic.Dictionary<string, int>
            ParcelsByDistrict = new System.Collections.Generic.Dictionary<string, int>();

        /// Busiest first, `name:count` joined by slashes — no spaces, because
        /// a verdict value may not contain one.
        public static string ParcelsByDistrictLine()
        {
            if (ParcelsByDistrict.Count == 0) return "none";
            var rows = new System.Collections.Generic.List<System.Collections.Generic.KeyValuePair<string, int>>(ParcelsByDistrict);
            rows.Sort((a, b) => b.Value.CompareTo(a.Value));
            var parts = new System.Collections.Generic.List<string>();
            foreach (var r in rows) parts.Add(r.Key + ":" + r.Value);
            return string.Join("/", parts);
        }

        static List<(Vector3 pos, Vector3 size)> BuildBlockSpecs()
        {
            var specs = new List<(Vector3, Vector3)>();
            TerraceChimneys.Clear();
            TerracedBlocks = 0; LegacyBlocks = 0; TerraceParcels = 0;
            ParcelsByDistrict.Clear();
            int bi = 0;
            foreach (var b in Ledger.Core.StreetMap.Blocks)
            {
                var rng = new System.Random(9001 + bi * 131);
                float inset = BlockSetback;               // pavement + a doorstep
                float minX = (float)b.MinX + inset, maxX = (float)b.MaxX - inset;
                float minZ = (float)b.MinZ + inset, maxZ = (float)b.MaxZ - inset;
                float w = maxX - minX, d = maxZ - minZ;
                if (w < 6 || d < 6) { bi++; continue; }

                // THE TERRACE PATH (town-plan.md T1). A block is a PERIMETER
                // of contiguous frontages around a rear yard, not detached
                // boxes floating in a field — the single change that turns
                // "objects on a plane" into "street-space between walls",
                // which is the whole enclosure argument of the plan.
                // Warehouse blocks keep the detached long-shed massing below:
                // a dock district genuinely is sheds and yard walls, and
                // terracing it would make it read as housing.
                var tpDistrict = Ledger.Core.StreetMap.DistrictAt(b.CentreX, b.CentreZ);
                if (TownPlanEnabled && tpDistrict != "Ironside")
                {
                    TerracedBlocks++;
                    TerraceBlock(specs, rng, minX, maxX, minZ, maxZ, tpDistrict);
                    bi++;
                    continue;
                }
                LegacyBlocks++;

                // Two to four along the longer axis, so a block reads as a
                // terrace of separate buildings rather than one solid slab.
                //
                // Except in Ironside, where the SAME rule would have been wrong:
                // a warehouse district is one or two long low sheds per block,
                // not a row of houses. Cheap to say and it does most of the work
                // of making the place read as somewhere goods are kept rather
                // than somewhere people live — long unbroken walls, few doors,
                // and nothing tall enough to have anybody looking down out of it.
                // Per-district massing (M14). One switch, four characters:
                // warehouses read long and low; Downtown reads TALL and
                // committee-shaped; Fairview low with garden gaps; the Strip
                // mid-rise and tight to the pavement; Gullwing low, wide and
                // half-empty. Cheap numbers doing district work.
                var districtName = Ledger.Core.StreetMap.DistrictAt(b.CentreX, b.CentreZ);
                bool warehouses = districtName == "Ironside";
                bool offices = districtName == "the Exchange";
                bool villas = districtName == "Fairview";
                bool resort = districtName == "Gullwing";
                bool alongX = w >= d;
                int count = warehouses ? 1 + rng.Next(2)
                    : offices ? 1 + rng.Next(2)
                    : villas ? 2 + rng.Next(2)
                    : resort ? 1 + rng.Next(2)
                    : 2 + rng.Next(3);
                float run = alongX ? w : d;
                float each = run / count;
                for (int k = 0; k < count; k++)
                {
                    float t = (k + 0.5f) / count;
                    float footprint = each * (warehouses ? 0.92f : offices ? 0.88f : villas ? 0.6f : resort ? 0.8f : 0.82f);
                    float depth = (alongX ? d : w) *
                        (warehouses ? 0.72f + 0.2f * (float)rng.NextDouble()
                         : offices ? 0.7f + 0.2f * (float)rng.NextDouble()
                         : villas ? 0.45f + 0.2f * (float)rng.NextDouble()
                         : resort ? 0.6f + 0.25f * (float)rng.NextDouble()
                         : 0.55f + 0.3f * (float)rng.NextDouble());
                    float height = warehouses ? 5f + (float)rng.NextDouble() * 4f
                        : offices ? 14f + (float)rng.NextDouble() * 10f
                        : villas ? 4f + (float)rng.NextDouble() * 3f
                        : resort ? 4f + (float)rng.NextDouble() * 5f
                        : 6f + (float)rng.NextDouble() * 11f;
                    var centre = alongX
                        ? new Vector3(minX + t * w, 0, (maxZ + minZ) / 2f)
                        : new Vector3((maxX + minX) / 2f, 0, minZ + t * d);
                    var size = alongX
                        ? new Vector3(footprint, height, depth)
                        : new Vector3(depth, height, footprint);

                    if (ClashesWithAuthored(centre, size)) continue;
                    specs.Add((centre, size));
                }
                bi++;
            }
            return specs;
        }

        /// ONE BLOCK AS A PERIMETER OF TERRACES (town-plan.md T1).
        ///
        /// Four rows, one per street-facing edge. The two Z-facing rows own
        /// the corners (full inset width); the X-facing rows start after
        /// them, so corners resolve without overlap and every corner of
        /// every block is a corner BUILDING — which is where the street
        /// name plates go in T2, exactly as a British council would.
        ///
        /// Parcels are contiguous — party walls, no gaps — except one alley
        /// mouth per block (deterministic), which is what keeps the rear
        /// yard reachable and gives the bins somewhere honest to stand.
        /// A parcel that would close an authored doorway is simply skipped:
        /// the gap it leaves reads as a yard gate, and a generated terrace
        /// must never shut a door the game opens.
        static void TerraceBlock(List<(Vector3 pos, Vector3 size)> specs,
                                 System.Random rng,
                                 float minX, float maxX, float minZ, float maxZ,
                                 string district)
        {
            // Row depths: shops want deeper plans than houses; offices
            // deeper still. The yard is whatever the middle has left.
            bool offices = district == "the Exchange";
            bool villas = district == "Fairview";
            bool resort = district == "Gullwing";

            float w = maxX - minX, d = maxZ - minZ;
            // DERIVED FROM THE BLOCK, CAPPED BY THE WISH-LIST — not the
            // other way round. RowDepth's 9-15m plans were written for
            // real-city blocks; THIS map's blocks are ~12.8m buildable
            // (26m grid, 8m roads, 2.6m setbacks), so demanding two 9m
            // rows plus a 4m yard produced one row on a good block and
            // nothing on Copper Row — terraceParcels=38 across 46 blocks,
            // measured, which is the empty city the stills were showing
            // all along. A terrace house is genuinely 4-5m deep all over
            // Britain; the deep plan is the luxury, not the norm.
            float halfAvail = (d - 3f) / 2f;
            float depthN = Mathf.Min(RowDepth(rng, offices, villas, resort), halfAvail);
            float depthS = Mathf.Min(RowDepth(rng, offices, villas, resort), halfAvail);
            bool deepEnough = depthN >= 4.2f;
            if (!deepEnough)
            {
                depthS = 0f;
                depthN = Mathf.Min(RowDepth(rng, offices, villas, resort),
                                   Mathf.Max(3.5f, d - 2.5f));
            }

            // Which edge carries the alley mouth, and where along it.
            int alleyEdge = rng.Next(4);
            float alleyT = 0.25f + 0.5f * (float)rng.NextDouble();

            // North and south rows: full width, corners included.
            TerraceRow(specs, rng, minX, maxX, maxZ, depthN, alongX: true, dir: +1f,
                       offices, villas, resort, alleyEdge == 0 ? alleyT : -1f, district);
            if (deepEnough)
                TerraceRow(specs, rng, minX, maxX, minZ, depthS, alongX: true, dir: -1f,
                           offices, villas, resort, alleyEdge == 1 ? alleyT : -1f, district);

            // East and west rows: between the corner buildings, with their
            // depths fitted to the width the same way.
            float z0 = minZ + (deepEnough ? depthS : 0f), z1 = maxZ - depthN;
            float sideAvail = (w - 3f) / 2f;
            if (z1 - z0 > 6f && sideAvail >= 4.2f)
            {
                float depthE = Mathf.Min(RowDepth(rng, offices, villas, resort), sideAvail);
                float depthW = Mathf.Min(RowDepth(rng, offices, villas, resort), sideAvail);
                TerraceRow(specs, rng, z0, z1, maxX, depthE, alongX: false, dir: +1f,
                           offices, villas, resort, alleyEdge == 2 ? alleyT : -1f, district);
                TerraceRow(specs, rng, z0, z1, minX, depthW, alongX: false, dir: -1f,
                           offices, villas, resort, alleyEdge == 3 ? alleyT : -1f, district);
            }
        }

        static float RowDepth(System.Random rng, bool offices, bool villas, bool resort) =>
            offices ? 12f + 3f * (float)rng.NextDouble()
            : villas ? 8f + 2f * (float)rng.NextDouble()
            : resort ? 9f + 2f * (float)rng.NextDouble()
            : 9f + 3f * (float)rng.NextDouble();

        /// One contiguous row of parcels from a0 to a1 whose front faces sit
        /// exactly on `frontCoord` — the building line. Contiguity is the
        /// point: `x` advances by exactly each parcel's width, so party
        /// walls touch, and the roofline steps because heights vary while
        /// the frontage never breaks.
        static void TerraceRow(List<(Vector3 pos, Vector3 size)> specs,
                               System.Random rng, float a0, float a1,
                               float frontCoord, float depth, bool alongX, float dir,
                               bool offices, bool villas, bool resort, float alleyT,
                               string district)
        {
            float run = a1 - a0;
            if (run < 5f || depth < 3.4f) return;
            // No alley in a run that cannot afford one: a 3m mouth in a
            // 12.8m row is a quarter of the block gone, and this map's
            // blocks are all near that size (the second thing
            // terraceParcels=58 taught).
            float alleyAt = alleyT > 0f && run >= 14f ? a0 + run * alleyT : float.MaxValue;
            bool alleyCut = false;

            float x = a0;
            while (a1 - x >= 4.5f)
            {
                if (!alleyCut && x >= alleyAt)
                {
                    x += 3.0f;      // the alley mouth: one cart wide, like the real ones
                    alleyCut = true;
                    if (a1 - x < 4.5f) break;
                }

                // A short run is ONE building filling all of it — this
                // map's blocks mostly hold a single frontage per edge, and
                // a 5.5-11m parcel lottery on a 12.8m run left slivers and
                // gaps where a solid wall should be.
                float remain = a1 - x;
                float pw = remain <= 12.5f ? remain : 5.5f + 5.5f * (float)rng.NextDouble();
                // Absorb a remainder too small to be a building into the
                // last parcel — a 2m sliver of house is a rendering error.
                if (a1 - (x + pw) < 4.5f) pw = a1 - x;

                float h = offices ? 12f + 10f * (float)rng.NextDouble()
                    : villas ? 5.5f + 2f * (float)rng.NextDouble()
                    : resort ? 5.5f + 3f * (float)rng.NextDouble()
                    : rng.NextDouble() < 0.55 ? 6.2f + 1.4f * (float)rng.NextDouble()   // two storeys
                                              : 8.6f + 1.8f * (float)rng.NextDouble(); // three

                var pos = alongX
                    ? new Vector3(x + pw / 2f, 0, frontCoord - dir * depth / 2f)
                    : new Vector3(frontCoord - dir * depth / 2f, 0, x + pw / 2f);
                var size = alongX
                    ? new Vector3(pw, h, depth)
                    : new Vector3(depth, h, pw);

                if (!ClashesWithAuthored(pos, size))
                {
                    specs.Add((pos, size));
                    TerraceParcels++;
                    // AND WHICH DISTRICT IT WENT IN — FROM THE BLOCK, NOT
                    // FROM THE PARCEL'S OWN POSITION.
                    //
                    // The block knows for certain: `BuildBlockSpecs` looked
                    // the district up once and passed it down. A parcel
                    // belongs to the block it fills, so there is nothing to
                    // infer from a coordinate.
                    //
                    // IT ALSO CAUGHT A MUCH LARGER BUG, AND THE FIRST TWO
                    // EXPLANATIONS FOR THAT BUG WERE BOTH WRONG. Asking
                    // `DistrictAt(pos)` returned `none` for 71% of 376
                    // parcels with Fairview absent entirely. I read that as
                    // the flat 12m margin being narrower than the 20-34m
                    // block spacing — plausible, and wrong. The real cause is
                    // in `DistrictAt` itself: it compared SCALED positions
                    // against UNSCALED avenue arrays, so four districts were
                    // looking 136-184m away from their own buildings. Fixed
                    // there. With the box in the right place, margins of 12,
                    // 20 and 26 assign all 52 blocks identically — the margin
                    // never mattered.
                    //
                    // THE SECOND WRONG EXPLANATION IS WORTH KEEPING TOO,
                    // because it delayed the real fix by a day. Widening the
                    // margin turned the traffic gate red and I recorded that
                    // as "the fix is not free, it wedges a bicycle". The gate
                    // was broken: it compared one vehicle's edge and position
                    // at two instants sixty seconds apart, so a car that drove
                    // a loop and came back read exactly like one that never
                    // moved. The flagged car had crossed EIGHT edges. Both the
                    // "it wedges traffic" reading and the ten-seed sweep that
                    // appeared to exonerate it came from that same instrument.
                    // Gate rewritten to read the whole window.
                    var pkey = string.IsNullOrEmpty(district) ? "none" : district.Replace(" ", "_");
                    ParcelsByDistrict.TryGetValue(pkey, out var had);
                    ParcelsByDistrict[pkey] = had + 1;
                    // A chimney stack on the leading party wall, on the
                    // ridge — the single cheapest silhouette signal a
                    // British terrace has. Offices get none: Downtown's
                    // skyline is tanks and tiers, not pots.
                    if (!offices && x > a0 + 0.5f)
                    {
                        var cpos = alongX
                            ? new Vector3(x + 0.45f, 0, pos.z)
                            : new Vector3(pos.x, 0, x + 0.45f);
                        TerraceChimneys.Add((cpos, h));
                    }
                }
                x += pw;
            }
        }

        /// Where a place's graybox mass STANDS — the one formula, shared by
        /// BuildDistrict (which draws it) and ClashesWithAuthored (which
        /// keeps terraces out of it). Two copies of this arithmetic would
        /// be the fourth "one idea, two implementations" on this file.
        /// False for unplanned places: they build nothing.
        public static bool PlaceMassOf(Ledger.Core.HookPlace place, out Vector3 pos, out Vector3 size)
        {
            pos = default; size = default;
            if (!place.Planned) return false;
            var stop = new Vector3((float)place.X, 0, (float)place.Z);
            var block = Ledger.Core.StreetMap.BlockAt(stop.x, stop.z);
            var dir = block != null
                ? new Vector3((float)block.CentreX - stop.x, 0, (float)block.CentreZ - stop.z).normalized
                : new Vector3(stop.x, 0, stop.z).normalized;
            if (dir.sqrMagnitude < 0.01f) dir = Vector3.forward;
            size = place.Kind == "home" ? new Vector3(9, 10, 8)
                : place.Kind == "landmark" ? new Vector3(10, 7, 9)
                : place.Kind == "business" ? new Vector3(7, 6, 7)
                : new Vector3(4, 3, 4); // corner: a shelter, not a building
            pos = stop + dir * (size.z / 2f + 2.5f);
            return true;
        }

        /// Keep clear of the bar and of every named place — a generated
        /// terrace must not close a door the game opens.
        ///
        /// REWRITTEN AGAINST THE MEASUREMENT (terraceParcels=38 across 46
        /// blocks). The old test was a halo around the place's STOP POINT —
        /// an authored kerbside coordinate — inflated by the parcel's own
        /// half-size, so one place erased half a row and 61 places erased
        /// the city. What actually needs protecting is the place's BUILT
        /// MASS (which stands ~6m into the block, via the shared formula
        /// above) and a doorway's worth of standing room at the stop. Box
        /// against box for the first; a 1.2m point margin for the second.
        static bool ClashesWithAuthored(Vector3 pos, Vector3 size)
        {
            float hx = size.x / 2f, hz = size.z / 2f;
            // The bar.
            if (Mathf.Abs(pos.x + 8f) < hx + 5f && Mathf.Abs(pos.z - 8f) < hz + 5f) return true;
            foreach (var place in Ledger.Core.HookMap.Places)
            {
                if (Mathf.Abs(pos.x - (float)place.X) < hx + 1.2f &&
                    Mathf.Abs(pos.z - (float)place.Z) < hz + 1.2f) return true;
                // 0.3 and not 1.0: on blocks this small a metre of margin
                // is the difference between a terrace that ABUTS the place
                // building — one continuous frontage, which is what a real
                // street does with its pub — and a block that stays empty
                // because nothing may stand near the only thing in it.
                if (PlaceMassOf(place, out var pp, out var ps) &&
                    Mathf.Abs(pos.x - pp.x) < hx + ps.x / 2f + 0.3f &&
                    Mathf.Abs(pos.z - pp.z) < hz + ps.z / 2f + 0.3f) return true;
            }
            return false;
        }

        static readonly List<(Vector3 pos, Vector3 size)> Masses = new List<(Vector3, Vector3)>();
        /// The primary building BODIES, recorded at creation — the honest
        /// population for any question about buildings as wholes. The first
        /// grounded-buildings sweep matched names instead and caught 553
        /// windows, mullions and shopfront heads, every one of which lives
        /// above ground by design: an allow-list of suffixes would decay
        /// the same way, and this list cannot, because the two call sites
        /// that make a body are the two lines that append to it.
        public static readonly List<GameObject> PrimaryMasses = new List<GameObject>();

        /// True when the straight XZ line from a to b crosses no building mass.
        /// Masses containing either endpoint are ignored so characters can step
        /// off a stoop or reach a doorway spot set flush against a wall.
        public static bool SegmentClear(Vector3 a, Vector3 b, float inflate = 0.9f)
        {
            foreach (var (pos, size) in Masses)
            {
                float hx = size.x / 2f + inflate, hz = size.z / 2f + inflate;
                if (InsideXZ(a, pos, hx, hz) || InsideXZ(b, pos, hx, hz)) continue;
                if (SegmentHitsBoxXZ(a, b, pos, hx, hz)) return false;
            }
            return true;
        }

        /// True when a single point stands clear of every building. SegmentClear
        /// deliberately ignores masses containing an endpoint (so a character can
        /// step off a stoop), which makes it useless for "is this spot free" —
        /// and parking a car inside a wall is exactly that question.
        public static bool PointClear(Vector3 p, float inflate = 0.9f)
        {
            foreach (var (pos, size) in Masses)
                if (InsideXZ(p, pos, size.x / 2f + inflate, size.z / 2f + inflate)) return false;
            return true;
        }

        /// The mass standing at (or within `r` of) a point, for signage that
        /// mounts on WALLS rather than posts (town-plan.md T2). First hit in
        /// list order, which is deterministic because the specs are.
        public static bool MassAt(Vector3 p, float r, out Vector3 pos, out Vector3 size)
        {
            foreach (var (mp, ms) in Masses)
                if (p.x > mp.x - ms.x / 2f - r && p.x < mp.x + ms.x / 2f + r &&
                    p.z > mp.z - ms.z / 2f - r && p.z < mp.z + ms.z / 2f + r)
                { pos = mp; size = ms; return true; }
            pos = default; size = default; return false;
        }

        static bool InsideXZ(Vector3 p, Vector3 c, float hx, float hz) =>
            p.x > c.x - hx && p.x < c.x + hx && p.z > c.z - hz && p.z < c.z + hz;

        static bool SegmentHitsBoxXZ(Vector3 a, Vector3 b, Vector3 c, float hx, float hz)
        {
            float dx = b.x - a.x, dz = b.z - a.z;
            float tmin = 0f, tmax = 1f;
            if (Mathf.Abs(dx) < 1e-6f) { if (a.x < c.x - hx || a.x > c.x + hx) return false; }
            else
            {
                float t1 = (c.x - hx - a.x) / dx, t2 = (c.x + hx - a.x) / dx;
                if (t1 > t2) { var t = t1; t1 = t2; t2 = t; }
                tmin = Mathf.Max(tmin, t1); tmax = Mathf.Min(tmax, t2);
                if (tmin > tmax) return false;
            }
            if (Mathf.Abs(dz) < 1e-6f) { if (a.z < c.z - hz || a.z > c.z + hz) return false; }
            else
            {
                float t1 = (c.z - hz - a.z) / dz, t2 = (c.z + hz - a.z) / dz;
                if (t1 > t2) { var t = t1; t1 = t2; t2 = t; }
                tmin = Mathf.Max(tmin, t1); tmax = Mathf.Min(tmax, t2);
                if (tmin > tmax) return false;
            }
            return true;
        }

        static void BuildBuildings()
        {
            var specs = Masses;
            string[] facades = { AssetLibrary.BrickRed, AssetLibrary.Plaster, AssetLibrary.BrickGrey, AssetLibrary.Concrete };
            int i = 0;
            foreach (var (pos, size) in specs)
            {
                // BY POSITION, NOT BY LOOP INDEX. `i % 4` marched
                // brick-plaster-brick-concrete in strict rotation down every
                // street — a repeating stripe, which is one of the strongest
                // greybox tells and became visible the day the textures did.
                // A position hash is just as deterministic (CI's pixel gates
                // depend on that) and reads as a town that grew, not a
                // pattern that was stamped.
                var facade = facades[FacadePick(pos)];
                var body = MakeBoxVaried($"Building_{i}", pos + new Vector3(0, size.y / 2f, 0), size, facade, pos);
                PrimaryMasses.Add(body);
                // Tile the façade at roughly one texture repeat per 3.5m so brick keeps a
                // consistent scale across differently-sized buildings.
                SetTiling(body, Mathf.Max(1, Mathf.RoundToInt(size.x / 3.5f)), Mathf.Max(1, Mathf.RoundToInt(size.y / 3.5f)));
                MakeBoxVaried($"Roof_{i}", pos + new Vector3(0, size.y + 0.15f, 0), new Vector3(size.x + 0.4f, 0.3f, size.z + 0.4f), AssetLibrary.Roof, pos);

                AddWindows($"Bldg{i}", pos, size);
                GroundFloor($"Bldg{i}", pos, size, OutwardFrom(pos));

                // Taller buildings get a stepped setback tier — breaks the flat-box
                // silhouette into something that reads as a real building profile.
                if (size.y >= 9f)
                {
                    var upper = new Vector3(size.x * 0.62f, 3.2f, size.z * 0.62f);
                    var upBase = size.y + 0.3f;
                    // Through the SAME variant+grade pick as the body (same
                    // `pos`, same hash) — plain MakeBox here gave the setback
                    // tier the base material while the body below it could be
                    // wearing the pack's `_b` texture, a mismatch inside one
                    // building that the grade pass would have widened.
                    var upBody = MakeBoxVaried($"Building_{i}_up", pos + new Vector3(0, upBase + upper.y / 2f, 0), upper, facade, pos);
                    SetTiling(upBody, Mathf.Max(1, Mathf.RoundToInt(upper.x / 3.5f)), 1);
                    MakeBox($"Roof_{i}_up", pos + new Vector3(0, upBase + upper.y + 0.1f, 0), new Vector3(upper.x + 0.3f, 0.2f, upper.z + 0.3f), AssetLibrary.Roof);
                    // A rooftop water tank / AC box for texture-of-life on the skyline.
                    MakeBox($"Roof_{i}_tank", pos + new Vector3(size.x * 0.2f, size.y + 0.9f, size.z * 0.15f), new Vector3(1.2f, 1.2f, 1.2f), AssetLibrary.Metal);
                }

                // THE BULK OF THE CITY, dressed. Only the district's named
                // places were getting clutter, which is a couple of dozen
                // pieces across seven districts — the block perimeters are
                // where nearly all the wall in this game actually is.
                //
                // Both sides, and they are different: the face pointing at
                // the road is a frontage somebody sweeps, and the face
                // pointing into the block is the back of it. That contrast is
                // free — the geometry already knows which is which — and it
                // is most of what makes a city feel like it has a front and a
                // back rather than being extruded on all sides.
                var outward = OutwardFrom(pos);
                DressFacade($"B{i}", pos, size, outward, hasDoor: true, prosperity: StreetFrontProsperity);
                DressFacade($"B{i}b", pos, size, -outward, hasDoor: false, prosperity: BackAlleyProsperity);
                FireEscape($"B{i}", pos, size, -outward);
                RearExtension($"B{i}", pos, size, -outward, facade);
                i++;
            }

            // The chimney stacks the terrace generator recorded: brick with
            // a capping slab, standing on the roofline at each party wall.
            // Emitted here because the generator makes specs and geometry
            // belongs to the build pass.
            int cn = 0, aerials = 0;
            foreach (var (cpos, baseY) in TerraceChimneys)
            {
                MakeBox($"Chimney_{cn}", cpos + new Vector3(0, baseY + 0.65f, 0),
                    new Vector3(0.85f, 1.3f, 0.85f), AssetLibrary.BrickRed);
                MakeBox($"ChimneyCap_{cn}", cpos + new Vector3(0, baseY + 1.38f, 0),
                    new Vector3(1.05f, 0.16f, 1.05f), AssetLibrary.Concrete);
                // CHIMNEY POTS — two squat clay cylinders per stack, which is
                // what turns "a box on a roof" into a British terrace at a
                // glance (M17.10, the Britishness pass).
                foreach (float px in new[] { -0.22f, 0.22f })
                    MakeBox($"ChimneyPot_{cn}_{(px < 0 ? "a" : "b")}",
                        cpos + new Vector3(px, baseY + 1.62f, 0),
                        new Vector3(0.20f, 0.34f, 0.20f), AssetLibrary.BrickRed);
                // AND A TV AERIAL ON MOST OF THEM — it is the late eighties,
                // so every roofline carries one. A mast lashed to the stack,
                // a boom, three elements; members kept chunky enough (3.5cm)
                // to survive 1280x720 rather than shimmer away like the first
                // cables did.
                if (Ledger.Core.Dressing.Roll(cpos.x, cpos.z, 51) < 0.62)
                {
                    float my = baseY + 1.4f;
                    var mast = cpos + new Vector3(0.38f, my + 0.9f, 0.1f);
                    MakeBox($"AerialMast_{cn}", mast,
                        new Vector3(0.035f, 1.8f, 0.035f), AssetLibrary.Metal);
                    float ay = my + 1.68f;
                    float yaw = (float)Ledger.Core.Dressing.Roll(cpos.x, cpos.z, 52);
                    // The boom points roughly one way per street (everyone
                    // aims at the same transmitter), with a little scatter.
                    bool ew = yaw < 0.7f;
                    var boomSize = ew ? new Vector3(1.1f, 0.035f, 0.035f)
                                      : new Vector3(0.035f, 0.035f, 1.1f);
                    MakeBox($"AerialBoom_{cn}",
                        new Vector3(mast.x, ay, mast.z), boomSize, AssetLibrary.Metal);
                    for (int el = 0; el < 3; el++)
                    {
                        float t = -0.42f + el * 0.36f;
                        var epos = ew
                            ? new Vector3(mast.x + t, ay, mast.z)
                            : new Vector3(mast.x, ay, mast.z + t);
                        var esize = ew ? new Vector3(0.035f, 0.035f, 0.55f - el * 0.09f)
                                       : new Vector3(0.55f - el * 0.09f, 0.035f, 0.035f);
                        MakeBox($"AerialEl_{cn}_{el}", epos, esize, AssetLibrary.Metal);
                    }
                    aerials++;
                }
                cn++;
            }
            ChimneyCount = cn;
            AerialCount = aerials;
        }

        /// How many chimney stacks the build pass actually emitted — the
        /// denominator smokeStacks was missing when it read 2.
        public static int ChimneyCount;

        /// How many of those stacks carry a TV aerial (M17.10 Britishness
        /// pass) — the roll is 0.62 so this should sit near two-thirds of
        /// ChimneyCount; zero with chimneys present means the branch died.
        public static int AerialCount;

        /// THE BACK OF A BLOCK, WHICH HAS BINS AND DRAINPIPES AND NO SHAPE.
        ///
        /// The last thing roadmap 17.7 still names: *"the back of a block gets
        /// bins and drainpipes but no geometry of its own"*. Both faces are
        /// already dressed differently — the street front is swept and the back
        /// is not — but a back wall is still a flat rectangle with clutter at
        /// the bottom of it, and what actually distinguishes the back of a
        /// building is what is bolted to it.
        ///
        /// A FIRE ESCAPE, because it is the highest silhouette per box there
        /// is. It is vertical where everything else here is horizontal, it
        /// breaks the wall at every floor, and it reads as "the back" from
        /// across a yard with no texture work at all. It is also the reason to
        /// look UP in an alley, which is the one direction this city currently
        /// gives nobody a reason to look.
        ///
        /// NEAR THE CORE ONLY, on the same ramp the window panes use — this is
        /// six boxes per building and the frame budget is already red on the
        /// game's own half.
        ///
        /// TWO FLOORS OR MORE. A fire escape on a shed is a joke, and the
        /// height test is the building's own rather than a new constant: the
        /// same 3m floor the windows are spaced on, which is why the number is
        /// read from there rather than written again here.
        public static int FireEscapes { get; private set; }

        /// Shopfront dividers drawn. Zero beside a non-zero `windowsShop` means
        /// the near-core test rejected every shopfront, which is a finding
        /// about the density ramp rather than about mullions.
        public static int Mullions { get; private set; }

        /// Surround pieces (jambs, headers, stallrisers) the V4 depth pass
        /// emitted — four per shop, so this over four disagreeing with the
        /// shop count means a branch died.
        public static int ShopSurrounds;
        /// Interior backdrops built behind shop glass (V4) — the denominator
        /// for "the voids are gone": zero with shops present is the wire
        /// broken, not the streets shopless.
        public static int ShopInteriors;

        /// Rear lean-to extensions actually built. The roadmap's last open
        /// line for 17.7 — "the back of a block gets bins and drainpipes
        /// but no geometry of its own" — is about building MASS: a back
        /// wall is still one flat rectangle. A lean-to is the cheapest
        /// honest answer: two boxes (body and a pitched-reading roof slab),
        /// deterministic per building, on roughly two of five near-core
        /// backs so alleys stop being corridors of flat brick.
        public static int LeanTos { get; private set; }

        static void RearExtension(string tag, Vector3 pos, Vector3 size,
                                  Vector3 back, string facade)
        {
            if (Ledger.Core.Dressing.NearestCore(pos.x, pos.z, DenseCores)
                > NearCoreMetres) return;
            // Two in five, deterministic from the tag like the escape's
            // shift, so the same buildings carry them every run and stills
            // stay comparable.
            if (Ledger.Core.Physique.Fraction(tag, 91) > 0.4) return;

            float faceOut = (Mathf.Abs(back.x) > 0.5f ? size.x : size.z) * 0.5f;
            var along = new Vector3(-back.z, 0, back.x);
            float wallLen = Mathf.Abs(along.x) > 0.5f ? size.x : size.z;
            // 40-70% of the wall, off centre — a full-width extension reads
            // as a second building, and centred reads as designed rather
            // than accreted, which the back of a block never is.
            float w = wallLen * (0.4f + 0.3f
                * (float)Ledger.Core.Physique.Fraction(tag, 92));
            float shift = (float)(Ledger.Core.Physique.Fraction(tag, 93) - 0.5)
                          * (wallLen - w) * 0.8f;
            const float depth = 2.0f, h = 2.6f;
            var at = pos + back * (faceOut + depth * 0.5f) + along * shift;
            MakeBox($"Lean_{tag}", at + new Vector3(0, h / 2f, 0),
                new Vector3(Mathf.Abs(along.x) > 0.5f ? w : depth, h,
                            Mathf.Abs(along.x) > 0.5f ? depth : w),
                facade);
            // The roof slab overhangs a touch and sits on the wall side
            // higher than the outer edge would — a flat box cannot pitch,
            // but an overhang plus the roof material reads as one from
            // street height, which is the only place anybody stands.
            MakeBox($"Lean_{tag}_roof", at + new Vector3(0, h + 0.08f, 0),
                new Vector3((Mathf.Abs(along.x) > 0.5f ? w : depth) + 0.3f,
                            0.16f,
                            (Mathf.Abs(along.x) > 0.5f ? depth : w) + 0.3f),
                AssetLibrary.Roof);
            LeanTos++;
        }

        static void FireEscape(string tag, Vector3 pos, Vector3 size, Vector3 back)
        {
            const float floorH = 3.0f;
            if (size.y < floorH * 2f) return;
            if (Ledger.Core.Dressing.NearestCore(pos.x, pos.z, DenseCores) > NearCoreMetres) return;

            // Against the wall it hangs on, offset out by its own depth so it
            // sits proud rather than inside the brick.
            const float depth = 1.1f, width = 2.2f, rail = 0.08f;
            float faceOut = (Mathf.Abs(back.x) > 0.5f ? size.x : size.z) * 0.5f;
            // ALONG the wall, off centre, because a fire escape is bolted where
            // the stairwell is and a stairwell is never in the middle of a
            // facade. Deterministic from the tag so it does not move between
            // runs and the stills stay comparable.
            var along = new Vector3(-back.z, 0, back.x);
            float shift = (float)(Ledger.Core.Physique.Fraction(tag, 53) - 0.5)
                          * ((Mathf.Abs(along.x) > 0.5f ? size.x : size.z) * 0.5f);
            var at = pos + back * (faceOut + depth * 0.5f) + along * shift;

            int floors = Mathf.Clamp(Mathf.FloorToInt(size.y / floorH), 2, 5);
            for (int f = 1; f < floors; f++)
            {
                float y = f * floorH;
                MakeBox($"Escape_{tag}_deck{f}", at + new Vector3(0, y, 0),
                    new Vector3(Mathf.Abs(along.x) > 0.5f ? width : depth, 0.08f,
                                Mathf.Abs(along.x) > 0.5f ? depth : width),
                    AssetLibrary.Metal);
                // The rail, which is what makes it read as a walkway rather
                // than a shelf.
                MakeBox($"Escape_{tag}_rail{f}", at + back * (depth * 0.45f) + new Vector3(0, y + 0.5f, 0),
                    new Vector3(Mathf.Abs(along.x) > 0.5f ? width : rail, rail,
                                Mathf.Abs(along.x) > 0.5f ? rail : width),
                    AssetLibrary.Metal);
                // And the run down to the deck below — one diagonal box, which
                // at this distance is a flight of stairs.
                //
                // THE TILT AXIS IS PERPENDICULAR TO THE TRAVEL, AND I WROTE IT
                // THE OTHER WAY ROUND FIRST. A fire escape's stair descends
                // ALONG the wall, so it drops in y while moving in `along` —
                // which means the rotation axis is the third one, `back`. My
                // first version rotated around `right` when `along` was x,
                // which tilts the stair in the plane it is already flat in and
                // leans it out of the wall instead of down it. Both branches
                // were inverted, in exactly the way the foot-plant phases were
                // this morning, and for the same reason: a ternary on an axis
                // reads as correct whichever way round it is written.
                //
                // Derived rather than branched, so there is nothing to invert:
                // `back` IS the perpendicular, it is already a unit vector, and
                // the sign of the lean follows the sign of `along`.
                // LONG IN THE DIRECTION IT TRAVELS, which is `along`, and
                // narrow across. Getting this the other way round makes a plank
                // lying sideways that the rotation then stands on its edge —
                // and it would have looked like a fire escape from far enough
                // away to pass a still, which is the worst kind of wrong.
                bool alongX = Mathf.Abs(along.x) > 0.5f;
                float runLen = floorH * 1.1f;
                var run = MakeBox($"Escape_{tag}_run{f}",
                    at + new Vector3(0, y - floorH * 0.5f, 0),
                    new Vector3(alongX ? runLen : 0.7f, 0.06f,
                                alongX ? 0.7f : runLen),
                    AssetLibrary.Metal);
                run.transform.rotation = Quaternion.AngleAxis(42f, back);
                FireEscapes++;
            }
        }

        /// Windows per floor on all four faces, sitting slightly proud of the
        /// façade. Collected so SetWindowsLit can make them glow after dusk.
        ///
        /// PANES, NOT BANDS, AND THAT IS THE FIX FOR THE NIGHT STILL. Each floor
        /// used to be ONE box across 82% of the face, so a lit building was a
        /// stack of solid glowing rectangles — which is exactly what
        /// `review_day1_night.jpg` shows, and it would look like that at any
        /// emission value. The bleached colour measured off the frame ledger
        /// (b/r 0.91 against the 0.45 asked for) is a SECOND, independent cause
        /// sitting on top of this one; fixing either alone leaves slabs.
        ///
        /// A window is a hole in a wall with wall on both sides of it. Splitting
        /// the band into panes with a pier between them costs one loop and is
        /// the difference between a lit building and a lit rectangle.
        ///
        /// PANE WIDTH IS DERIVED, NOT PICKED: the count is chosen so a pane
        /// lands near 1.4m, which is a domestic window, and then the run is
        /// divided evenly so a wide façade gets more windows rather than wider
        /// ones. That is the property that makes buildings of different sizes
        /// look like the same city.
        static void AddWindows(string tag, Vector3 pos, Vector3 size)
        {
            const float floorH = 3.0f, bandH = 1.3f, proud = 0.04f, target = 1.4f, gap = 0.55f;
            float runX = size.x * 0.82f, runZ = size.z * 0.82f;

            // AND SPLIT ONLY WHERE SOMEBODY IS STANDING. Panes are ~4x the
            // window renderers of a band, and this runs on a GPU-less runner
            // already spending ~335ms a frame in the software rasteriser — a
            // change that improves the near view and times the sim step out has
            // not improved anything.
            //
            // The test is the one the facades already use — `NearCoreMetres`,
            // the constant this file defines as "within this of a core counts as
            // a dense district for the gate". Reused rather than reinvented: my
            // first version thresholded `DetailAt` at 0.5, which is a number I
            // picked, and `DetailAt` does not even range over 0..1 (it floors at
            // 0.34), so 0.5 was not the midpoint of anything. A far building
            // keeps the single band it has always had, where it is a smudge in
            // fog and the difference is invisible.
            bool near = Ledger.Core.Dressing.NearestCore(pos.x, pos.z, DenseCores) <= NearCoreMetres;
            if (near) WindowPanes++; else WindowBands++;
            int nx = near ? Mathf.Max(1, Mathf.RoundToInt(runX / (target + gap))) : 1;
            int nz = near ? Mathf.Max(1, Mathf.RoundToInt(runZ / (target + gap))) : 1;
            float paneX = (runX - gap * (nx - 1)) / nx;
            float paneZ = (runZ - gap * (nz - 1)) / nz;

            // A PARTY WALL IS NOT A FACADE (town-plan.md T1). Terrace parcels
            // touch, so a face can be another building — and where rooflines
            // step, a window band on that face floats over the neighbour's
            // roof as glass on a blank gable. Sample just outside each pane:
            // inside any mass's footprint means the wall is shared and stays
            // brick. Height is deliberately ignored — the stub of party wall
            // ABOVE a shorter neighbour is a gable, and gables are blank.
            // (Tiers are safe: they never come through here.) Gated on the
            // flag so the legacy path stays byte-identical for the revert.
            bool Open(float sx, float sz)
            {
                if (!TownPlanEnabled) return true;
                foreach (var (mp, ms) in Masses)
                    if (sx > mp.x - ms.x / 2f && sx < mp.x + ms.x / 2f &&
                        sz > mp.z - ms.z / 2f && sz < mp.z + ms.z / 2f) return false;
                return true;
            }

            int floor = 0;
            for (float y = 2.0f; y < size.y - 1.0f; y += floorH, floor++)
            {
                // GROUND FLOOR IS DIFFERENT, because on a real street it is: a
                // shopfront is one wide light and the flats above it are a row
                // of small ones. One `if` buys the single most legible thing a
                // block of buildings can have, which is a bottom.
                bool ground = floor == 0;
                for (int k = 0; k < (ground ? 1 : nz); k++)
                {
                    float off = ground ? 0f : -runZ / 2f + paneZ / 2f + k * (paneZ + gap);
                    float w = ground ? runZ * 0.92f : paneZ;
                    if (Open(pos.x + size.x / 2f + 0.3f, pos.z + off))
                    {
                        var wc = new Vector3(pos.x + size.x / 2f + proud, y, pos.z + off);
                        var ws = new Vector3(0.08f, bandH, w);
                        AddWindow(WinBox($"{tag}_win_xP_{floor}_{k}", wc, ws), ground);
                        if (near) Sill($"{tag}_sill_xP_{floor}_{k}", wc, ws, bandH);
                    }
                    if (Open(pos.x - size.x / 2f - 0.3f, pos.z + off))
                    {
                        var wc = new Vector3(pos.x - size.x / 2f - proud, y, pos.z + off);
                        var ws = new Vector3(0.08f, bandH, w);
                        AddWindow(WinBox($"{tag}_win_xN_{floor}_{k}", wc, ws), ground);
                        if (near) Sill($"{tag}_sill_xN_{floor}_{k}", wc, ws, bandH);
                    }
                }
                for (int k = 0; k < (ground ? 1 : nx); k++)
                {
                    float off = ground ? 0f : -runX / 2f + paneX / 2f + k * (paneX + gap);
                    float w = ground ? runX * 0.92f : paneX;
                    if (Open(pos.x + off, pos.z + size.z / 2f + 0.3f))
                    {
                        var wc = new Vector3(pos.x + off, y, pos.z + size.z / 2f + proud);
                        var ws = new Vector3(w, bandH, 0.08f);
                        AddWindow(WinBox($"{tag}_win_zP_{floor}_{k}", wc, ws), ground);
                        if (near) Sill($"{tag}_sill_zP_{floor}_{k}", wc, ws, bandH);
                    }
                    if (Open(pos.x + off, pos.z - size.z / 2f - 0.3f))
                    {
                        var wc = new Vector3(pos.x + off, y, pos.z - size.z / 2f - proud);
                        var ws = new Vector3(w, bandH, 0.08f);
                        AddWindow(WinBox($"{tag}_win_zN_{floor}_{k}", wc, ws), ground);
                        if (near) Sill($"{tag}_sill_zN_{floor}_{k}", wc, ws, bandH);
                    }
                }
            }
        }

        /// A LEDGE UNDER EVERY PANE, which is the quality ladder's named
        /// next rung for buildings ("window reveals/sills relief").
        ///
        /// A facade of flush panes is the flattest thing in these frames:
        /// the windows stand 0.08 proud of the brick and cast nothing. A
        /// sill projects far enough to throw a hard line across the wall
        /// under each opening, and a row of those lines is most of what
        /// reads as MASONRY rather than as a painted elevation. One box per
        /// window, no new material, no new pass.
        ///
        /// NEAR BUILDINGS ONLY. Far blocks carry a single window BAND per
        /// face by design — a smudge in fog — and a sill under a band is a
        /// ledge under a stripe, which is not a thing. `near` is the flag
        /// the pane/band split already uses, so this inherits that decision
        /// rather than inventing a second distance rule.
        ///
        /// Sized off the window it serves rather than by constants: as wide
        /// as the opening, 0.06 tall, projecting 0.20 against the pane's
        /// 0.08 so the ledge clears the glass and the shadow lands on
        /// brick. Collider dropped — a sill is scenery, and the window's
        /// own collider went for the same reason after the courier spent
        /// 197 ticks against one.
        /// Read by the sim: a sill pass that silently placed none and one
        /// that dressed the town read identically from a still at street
        /// distance (rule 3b).
        public static int SillCount;
        static void Sill(string name, Vector3 winCentre, Vector3 winSize, float bandH)
        {
            bool alongZ = winSize.x < winSize.z;
            var sz = alongZ ? new Vector3(0.20f, 0.06f, winSize.z * 1.02f)
                            : new Vector3(winSize.x * 1.02f, 0.06f, 0.20f);
            var at = new Vector3(winCentre.x, winCentre.y - bandH / 2f - 0.03f, winCentre.z);
            var go = MakeBox(name, at, sz, AssetLibrary.Concrete);
            var c = go.GetComponent<Collider>();
            if (c != null) Object.Destroy(c);
            // SHADOW CASTING STAYS ON, AND THE EXPERIMENT THAT TURNED IT
            // OFF IS REVERTED HERE RATHER THAN LEFT IN.
            //
            // The claim was that 2,133 new casters in the sun's shadow map
            // were most of the day's 4.4ms frame drift. Turning them off
            // moved `meanFrame` 29.43 -> 30.27 (the wrong way) and the
            // ladder's shadow rung 6.4 -> 6.1ms. It bought nothing, so a
            // sill that casts no shadow is strictly worse for free.
            //
            // WHAT THE SERIES ACTUALLY SAYS, read across sixteen landed
            // desktop runs: nine at 26.5-27.7, then a step to 28.4-28.9 on
            // the build that added sills — so the sills cost ~1.5ms, and
            // it is the extra renderers, not their shadows. The 29.4 and
            // 30.3 after that are NOISE: 29.43 came off a
            // COMMENT-ONLY build, which cannot cost a millisecond.
            //
            // So `meanFrame` carries about 1ms of run-to-run variance on
            // this machine, and a single-run difference of that size means
            // nothing. Three attributions today were made against
            // differences at or under it.
            SillCount++;
        }

        /// A STREET-LEVEL FLOOR THAT IS NOT THE SAME AS THE FLOORS ABOVE IT.
        ///
        /// This is the last thing the roadmap's 17.7 actually names, once
        /// "buildings are cubes" turned out to be wrong in both directions:
        /// they are box assemblies with roofs, setbacks and rooftop tanks, and
        /// what they were missing was a BOTTOM. Every façade ran the same window
        /// band from pavement to parapet, so a five-storey block and a shop read
        /// identically and nothing told you where you could go in.
        ///
        /// Three pieces, all cheap, all silhouette:
        ///
        ///   a fascia   the horizontal band a shop's name sits on, which is what
        ///              separates the commercial floor from the flats above it
        ///   a door     a recess in the street-facing wall — the single strongest
        ///              signal that a building is enterable, and this game is
        ///              about places you can and cannot get into
        ///   a cornice  a lip at the roofline. A flat box meeting the sky is the
        ///              most graybox thing a building can do; a 25cm overhang
        ///              casts a shadow line and costs one box.
        ///
        /// STREET SIDE ONLY. The back of a block is a back — `DressFacade`
        /// already makes that distinction with bins and drainpipes, and putting
        /// a shopfront on the alley face would undo it.
        static void GroundFloor(string tag, Vector3 pos, Vector3 size, Vector3 outward)
        {
            // Which axis the street face lies on, and how wide it is.
            bool alongX = Mathf.Abs(outward.x) > 0.5f;
            float width = alongX ? size.z : size.x;
            float depth = alongX ? size.x : size.z;
            var face = pos + outward * (depth * 0.5f);

            // WHAT KIND OF PLACE THIS IS. Until now every mass in the city got
            // the same fascia, the same door and the same cornice, so a
            // five-storey block, a corner shop and a dock warehouse were one
            // object at three sizes — and a street read as repetition however
            // well each individual wall was dressed. This function's own note
            // says "nothing told you where you could go in"; that was solved
            // for one building and never for the difference between buildings.
            //
            // Prosperity comes from the same ramp `DressFacade` uses for
            // clutter, so the two descriptions of one street agree by
            // construction: a frontage with shops is a frontage somebody
            // sweeps, and a warehouse stands where the bins pile up.
            bool nearCore = Ledger.Core.Dressing.NearestCore(face.x, face.z, DenseCores)
                            <= NearCoreMetres;
            // STREET-FRONT PROSPERITY ALWAYS, because this function dresses
            // the street front — that is stated at the top of it. Passing the
            // back-alley figure to every frontage away from a core told
            // `KindAt` those walls were back alleys and turned forty percent of
            // them into warehouses.
            var kind = Ledger.Core.Dressing.KindAt(face.x, face.z,
                StreetFrontProsperity, nearCore);
            PremisesBuilt[(int)kind]++;
            // AND BY DISTRICT, BECAUSE THE TOTAL CANNOT ANSWER THE QUESTION
            // THE DISTRICT TABLE ASKS.
            //
            // `premises=[shop77 house130 tenement159 shed10]` says the town
            // has ten sheds. It cannot say whether they are all in Ironside,
            // whose brief is places without witnesses and whose share is set
            // to 0.55, or scattered through Fairview where the share is zero.
            // The whole point of keying the rule on district is a claim about
            // WHERE, and a total is blind to where by construction.
            //
            // Also the rule-6 check on the table itself: `KindAt` is asserted
            // in CoreTests over Ironside's real bounds, but that proves the
            // FUNCTION returns sheds, not that the Game layer ever asks it
            // about an Ironside wall. Only a per-district count taken at the
            // build can say the table reaches the world.
            {
                var dn = Ledger.Core.StreetMap.DistrictAt(face.x, face.z);
                var dkey = string.IsNullOrEmpty(dn) ? "none" : dn.Replace(" ", "_");
                PremisesByDistrict.TryGetValue(dkey, out var row);
                if (row == null) PremisesByDistrict[dkey] = row = new int[4];
                row[(int)kind]++;
            }

            // The fascia: a band over the shopfront, at the height the ground
            // floor ends. Proud of the wall so it reads as a ledge rather than
            // as paint. A house does not get one — a signboard over somebody's
            // front room is the fastest way to make a residential street look
            // like a high street.
            // MULLIONS, BECAUSE A LIT SHOPFRONT IS OTHERWISE ONE GLOWING SLAB.
            //
            // The ground floor is deliberately ONE wide light — that decision
            // is right and it is what makes a block read as having a bottom.
            // But `SetWindowsLit` gave it an emissive tonight, and the night
            // still shows the result: the two biggest bright objects in the
            // frame are ground-floor rectangles two metres by six, glowing flat.
            // Real shopfront glass is divided; the dividers are why a lit window
            // reads as a window rather than as a light box.
            //
            // THREE THIN DARK BOXES OVER THE GLASS, not a change to the glass.
            // The window stays one renderer, so `Windows` and its occupancy
            // logic are untouched and there is nothing to keep in step — the
            // mullions are geometry in front of it, which is what a mullion
            // physically is.
            //
            // STREET SIDE ONLY and near the core only, on the same two tests
            // everything else at this level uses.
            if (Ledger.Core.Dressing.NearestCore(pos.x, pos.z, DenseCores) <= NearCoreMetres)
            {
                var alongDir = alongX ? new Vector3(0, 0, 1) : new Vector3(1, 0, 0);
                for (int m = 1; m <= 3; m++)
                {
                    float t = -width * 0.5f + width * (m / 4f);
                    var bar = MakeBox($"{tag}_mullion{m}",
                        face + outward * 0.06f + alongDir * t + new Vector3(0, 2.0f, 0),
                        new Vector3(alongX ? 0.10f : 0.12f, 2.6f, alongX ? 0.12f : 0.10f),
                        AssetLibrary.Metal);
                    var col = bar.GetComponent<Collider>();
                    // NO COLLIDER, because a mullion is 10cm of trim and a
                    // player who can be stopped by it is a player fighting the
                    // scenery. `StreetFurniture` strips its own for the same
                    // reason; this file has no helper, so it is done here.
                    if (col != null) Object.Destroy(col);
                    Mullions++;
                }
            }

            if (Ledger.Core.Dressing.HasFascia(kind))
            {
                var fasciaSize = alongX
                    ? new Vector3(0.25f, 0.55f, width * 0.9f)
                    : new Vector3(width * 0.9f, 0.55f, 0.25f);
                MakeBox($"{tag}_fascia", face + new Vector3(0, 3.5f, 0), fasciaSize,
                        AssetLibrary.Roof);

                // TOWN-PLAN.MD T2 item 4: the NAME on the board. A fascia
                // with no name is "commercial-ish box"; a painted trade name
                // is what makes it a shop you could be sent to. Deterministic
                // from position (the same city every run, CI stills stay
                // comparable), trade tables split by kind — a warehouse gets
                // a company, not a chip shop. 26 shops + 12 sheds in the
                // last verdict, so this is ~38 TextMeshes, not the 144 the
                // stop signs refused to spend.
                if (TownPlanEnabled)
                {
                    var names = kind == Ledger.Core.Dressing.Premises.Warehouse
                        ? WarehouseNames : ShopNames;
                    int pick = System.Math.Abs((int)(pos.x * 31 + pos.z * 7)) % names.Length;
                    var tgo = new GameObject($"{tag}_fascia_name");
                    // Local -z is what a translated WorldText copy reads
                    // from (see StreetFurniture.Label): aim it outward.
                    float yaw = Mathf.Atan2(-outward.x, -outward.z) * Mathf.Rad2Deg;
                    tgo.transform.position = face + outward * 0.16f + new Vector3(0, 3.5f, 0);
                    tgo.transform.rotation = Quaternion.Euler(0, yaw, 0);
                    tgo.transform.Translate(0, 0, -0.05f, Space.Self);
                    var tm = tgo.AddComponent<TextMesh>();
                    tm.text = names[pick];
                    tm.characterSize = 0.062f;
                    tm.fontSize = 64;
                    tm.anchor = TextAnchor.MiddleCenter;
                    tm.alignment = TextAlignment.Center;
                    tm.color = new Color(0.88f, 0.85f, 0.74f);
                    WorldText.Adopt(tm);
                    ShopNamesPainted++;
                }
            }

            // THE SHOPFRONT SURROUND (M17.10 V4) — depth, at last. Every
            // frontage has been a flat plane with paint-thin dressing, and
            // the reference frames' ground floors are LAYERED: glass behind
            // a frame, a stallriser under it, all of it throwing real
            // shadow lines now the sun works. Proud geometry rather than a
            // true recess, deliberately: moving the glass plane would touch
            // `Windows` and the occupancy logic, and a 25cm-proud surround
            // reads as the same depth from across a street — the fascia
            // above made the identical trade and reads as a ledge.
            //
            // Jambs, header, and the stallriser — the low panel under the
            // glass that every British shopfront actually has. Dark trim,
            // no colliders (10cm of trim must not stop a player).
            if (kind == Ledger.Core.Dressing.Premises.Shop)
            {
                var along = alongX ? new Vector3(0, 0, 1) : new Vector3(1, 0, 0);
                // PAINTED JOINERY, NOT ROOF FELT. The noon facade census
                // (08d6472) read the dark left third as 39% mat_roof — and
                // this surround was most of it: jambs, head and stall riser
                // in the palette's darkest material (~0.026 linear) on the
                // most street-facing joinery the game has. A British
                // shopfront surround is PAINTED — the awning palette's
                // hues, lifted to joinery values. One colour per shop,
                // hashed like the awning's. Opaque() rather than Tint(),
                // because an MPB colour MULTIPLIES onto Roof's dark-baked
                // texture and can only darken further — the same trap as
                // the glTFast furniture, one shader family over.
                var joinery = ShopfrontPaints[
                    System.Math.Abs((int)(pos.x * 13 + pos.z * 5)) % ShopfrontPaints.Length];
                void Trim(string part, Vector3 at, Vector3 sz)
                {
                    var b = MakeBox($"{tag}_{part}", at, sz, AssetLibrary.Roof);
                    b.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Opaque(joinery);
                    var c2 = b.GetComponent<Collider>();
                    if (c2 != null) Object.Destroy(c2);
                    ShopSurrounds++;
                }
                float half = width * 0.45f;
                var jambSz = alongX ? new Vector3(0.28f, 2.9f, 0.22f)
                                    : new Vector3(0.22f, 2.9f, 0.28f);
                Trim("jambL", face + outward * 0.12f - along * half + new Vector3(0, 1.45f, 0), jambSz);
                Trim("jambR", face + outward * 0.12f + along * half + new Vector3(0, 1.45f, 0), jambSz);
                var headSz = alongX ? new Vector3(0.26f, 0.24f, width * 0.92f)
                                    : new Vector3(width * 0.92f, 0.24f, 0.26f);
                Trim("head", face + outward * 0.12f + new Vector3(0, 2.95f, 0), headSz);
                var stallSz = alongX ? new Vector3(0.24f, 0.55f, width * 0.92f)
                                     : new Vector3(width * 0.92f, 0.55f, 0.24f);
                Trim("stall", face + outward * 0.11f + new Vector3(0, 0.30f, 0), stallSz);

                // THE ROOM BEHIND THE GLASS (M17.10 V4 — the flat black
                // shopfront void, named in the first V0 pass and open
                // since). The walls are solid boxes, so a true recess would
                // sit inside the brick; instead the interior is LAYERED
                // where the depth cue actually reads from the street: a
                // warm backdrop just off the wall, two dark shelf
                // silhouettes in front of it, the real glass, mullions and
                // trim in front of those. At night the backdrop registers
                // like any shop window and glows on shop hours, and the
                // silhouettes carve it into an interior; by day it is a dim
                // warm room behind dark glass. The proper recessed room is
                // the ladder's next rung, not this one.
                var inw = alongX ? new Vector3(0.03f, 2.3f, width * 0.86f)
                                 : new Vector3(width * 0.86f, 2.3f, 0.03f);
                var room = MakeBox($"{tag}_interior", face + outward * 0.02f
                        + new Vector3(0, 1.75f, 0), inw, AssetLibrary.Interior);
                var rc = room.GetComponent<Collider>();
                if (rc != null) Object.Destroy(rc);
                AddWindow(room.GetComponent<Renderer>(), shopfront: true);
                for (int sh = 0; sh < 2; sh++)
                {
                    var shSz = alongX ? new Vector3(0.04f, 0.10f, width * 0.78f)
                                      : new Vector3(width * 0.78f, 0.10f, 0.04f);
                    var shelf = MakeBox($"{tag}_shelf{sh}", face + outward * 0.03f
                            + new Vector3(0, 1.25f + sh * 0.6f, 0), shSz, AssetLibrary.Roof);
                    var sc2 = shelf.GetComponent<Collider>();
                    if (sc2 != null) Object.Destroy(sc2);
                }
                ShopInteriors++;
            }

            // An awning over a shop window (kit mesh, town-plan T2): scaled
            // to the frontage, oriented by its bounds the way the lamps are,
            // tinted to the district's weathered canvas. A miss just leaves
            // the fascia and mullions, which already read as a shopfront.
            if (TownPlanEnabled && kind == Ledger.Core.Dressing.Premises.Shop)
            {
                var akey = width > 6f ? "city_kit_commercial_detail_awning_wide"
                                      : "city_kit_commercial_detail_awning";
                var awn = AssetLibrary.TryInstantiateProp(akey,
                    face + outward * 0.1f + new Vector3(0, 2.75f, 0), Quaternion.identity);
                if (awn != null)
                {
                    var rends = awn.GetComponentsInChildren<Renderer>();
                    if (rends.Length == 0) Object.Destroy(awn);
                    else
                    {
                        var ab = rends[0].bounds;
                        foreach (var r in rends) ab.Encapsulate(r.bounds);
                        float along = alongX ? ab.size.z : ab.size.x;
                        float wantAlong = width * 0.7f;
                        if (along > 0.2f) awn.transform.localScale *= wantAlong / along;
                        ab = rends[0].bounds;
                        foreach (var r in rends) ab.Encapsulate(r.bounds);
                        var ao = ab.center - awn.transform.position; ao.y = 0;
                        if (ao.sqrMagnitude > 0.01f)
                        {
                            float have = Mathf.Atan2(ao.x, ao.z) * Mathf.Rad2Deg;
                            float want = Mathf.Atan2(outward.x, outward.z) * Mathf.Rad2Deg;
                            awn.transform.rotation = Quaternion.Euler(0, want - have, 0);
                        }
                        var ampb = new MaterialPropertyBlock();
                        ampb.SetColor("_Color", AwningPaints[
                            System.Math.Abs((int)(pos.x * 13 + pos.z * 5)) % AwningPaints.Length]);
                        foreach (var r in rends) { r.SetPropertyBlock(ampb); }
                        foreach (var c in awn.GetComponentsInChildren<Collider>())
                            Object.Destroy(c);
                    }
                }
            }

            // The door: narrow, tall, set INTO the wall rather than onto it, so
            // it reads as an opening at any angle instead of a panel that
            // disappears when you are not square to it.
            //
            // I ADDED A SECOND DOOR SYSTEM ON 3 AUGUST BEFORE READING THIS
            // FUNCTION. The roadmap said 17.7 still owed "cornices, and doors
            // as geometry"; both were already here, three lines apart, and I
            // built a `Clutter.Door` in Core with four tests to put a second
            // door on the same wall as this one. Rule 3, exactly: when your own
            // analysis says something is missing, OPEN THE FILE. The duplicate
            // is reverted and the two improvements it did carry are folded in
            // here, where the one door already was.
            // WIDTH FROM THE PREMISES, and the height with it: a loading door
            // has to take a cart, and a cart is not 2.2m of headroom short.
            float dwid = (float)Ledger.Core.Dressing.DoorWidth(kind);
            float dhgh = kind == Ledger.Core.Dressing.Premises.Warehouse ? 3.2f : 2.2f;
            var doorSize = alongX
                ? new Vector3(0.30f, dhgh, dwid)
                : new Vector3(dwid, dhgh, 0.30f);
            // WOOD AND DARKER, not bare metal. A door the same value as its
            // wall is a panel; the recess only reads as an opening if there is
            // a shadow in it, which is the same argument the window piers won.
            var leaf = MakeBox($"{tag}_door", face - outward * 0.12f
                    + new Vector3(0, dhgh * 0.5f, 0), doorSize, AssetLibrary.Wood);
            // A LEAF THAT CAN ACTUALLY SWING. The box is centred on the
            // opening, and a door hinges on its EDGE — rotating this
            // transform would pivot it about its middle and read as a
            // turnstile. So it gets a hinge parent at one jamb and hangs
            // off it; `DoorHost` rotates the hinge and never touches the
            // leaf. Costs one empty GameObject per door and no renderer.
            // Its own offset, not the jambs' `off` — that is declared below
            // this point and reusing it would be a use-before-declaration.
            // Same arithmetic, half the leaf's width along the wall.
            var hingeAxis = alongX ? new Vector3(0, 0, 1) : new Vector3(1, 0, 0);
            var hingeAt = face - outward * 0.12f
                        + hingeAxis * (alongX ? doorSize.z : doorSize.x) * 0.5f
                        + new Vector3(0, dhgh * 0.5f, 0);
            var hinge = new GameObject($"{tag}_hinge");
            hinge.transform.position = hingeAt;
            hinge.transform.rotation = Quaternion.LookRotation(outward, Vector3.up);
            leaf.transform.SetParent(hinge.transform, true);
            // NO COLLIDER ON A LEAF THAT SWINGS, and this is a regression I
            // introduced today rather than a tidy-up. `MakeBox` builds on
            // `CreatePrimitive`, which ships a BoxCollider; a static door
            // recessed 12cm into the facade kept that collider harmlessly
            // inside the wall. The moment the hinge turns it, roughly a metre
            // of collider sweeps out across the PAVEMENT — the surface the
            // whole crowd walks on.
            //
            // Measured, not suspected: `shiftTrace` on the red `dayJob` run
            // reads `d13:noaccept ... stalled:733 of ticks:1257 ...
            // on:Bldg69_door@0.2m`. The courier spent 58% of the run pressed
            // against a door at twenty centimetres, never got nearer than
            // 6.3m to the job board, and missed the noon cutoff.
            //
            // Safe to remove, checked rather than assumed: the leaf sits
            // INSIDE the facade, so the building's own collider still stops
            // anyone walking at it; `DoorHost` uses distances, not raycasts;
            // and `WinBox` already does exactly this, for exactly this
            // reason. A door is scenery you walk through a doorway of, not a
            // thing to be blocked by — especially one that opens for you.
            foreach (var dc in leaf.GetComponentsInChildren<Collider>())
                Object.Destroy(dc);
            DoorHost.Register(hinge.transform);

            var lr = leaf.GetComponent<Renderer>();
            var lmpb = new MaterialPropertyBlock();
            lr.GetPropertyBlock(lmpb);
            lmpb.SetColor("_Color", new Color(0.13f, 0.11f, 0.10f));
            lr.SetPropertyBlock(lmpb);

            // AND A JAMB EACH SIDE, proud of the wall. One box per side rather
            // than a surround, because a surround needs a hole in the wall and
            // this whole city is boxes. It is what turns a dark rectangle into
            // a doorway at a glance from across the street.
            var alongAxis = alongX ? new Vector3(0, 0, 1) : new Vector3(1, 0, 0);
            var jambSize = alongX
                ? new Vector3(0.22f, dhgh + 0.16f, 0.14f)
                : new Vector3(0.14f, dhgh + 0.16f, 0.22f);
            var off = alongAxis * (alongX ? doorSize.z : doorSize.x) * 0.5f
                      + alongAxis * 0.07f;
            MakeBox($"{tag}_jambA", face + off + new Vector3(0, dhgh * 0.54f, 0), jambSize,
                    AssetLibrary.Concrete);
            MakeBox($"{tag}_jambB", face - off + new Vector3(0, dhgh * 0.54f, 0), jambSize,
                    AssetLibrary.Concrete);
            // And a step (town-plan T2): a threshold is the cheapest thing
            // that says a door is USED. Houses especially — a British
            // terrace is a rhythm of doorsteps.
            if (TownPlanEnabled)
                MakeBox($"{tag}_step", face + outward * 0.24f + new Vector3(0, 0.07f, 0),
                    alongX ? new Vector3(0.5f, 0.14f, dwid + 0.35f)
                           : new Vector3(dwid + 0.35f, 0.14f, 0.5f),
                    AssetLibrary.Concrete);
            Doors++;

            // The cornice: a lip at the parapet, all the way round, because a
            // flat box meeting the sky is what makes a skyline read as
            // untextured geometry.
            MakeBox($"{tag}_cornice", pos + new Vector3(0, size.y - 0.35f, 0),
                    new Vector3(size.x + 0.5f, 0.35f, size.z + 0.5f), AssetLibrary.Roof);
        }

        /// Anything else that should glow after dusk — a vehicle's headlamps,
        /// for instance. Registered rather than found, so the night pass stays a
        /// single list walk instead of a scene search.
        public static void RegisterNightLight(Renderer r)
        {
            // NOT A SHOPFRONT. A headlamp is on because a car is being driven,
            // which is neither a flat's occupancy nor a shop's opening hours —
            // so it takes the residential path and is lit whenever the lamps
            // are, which is what it did before either schedule existed.
            if (r == null) return;
            AddWindow(r, shopfront: false);
            // No emission-map override any more — no map is bound anywhere
            // (see AddWindow), and a headlamp's bounds are far under the
            // band threshold, so the scale lands at full strength on its
            // own.
        }

        /// How many window renderers the city built, and how many of those are
        /// panes rather than bands.
        ///
        /// PRINTED BECAUSE THE COST IS THE RISK. Panes are roughly four times
        /// the renderers of a band and this runs on a software rasteriser, so
        /// the next run's `meanFrame` against the 335ms before it is the
        /// measurement that says whether the near/far split was cut in the right
        /// place. Guessing that from the still is how three correct things got
        /// condemned in one night.
        public static int WindowPanes, WindowBands;

        /// Keep the two lists in step in ONE place. Two `Add` calls at four
        /// sites is four chances for them to drift by one, and an off-by-one
        /// here would light the wrong windows for ever with nothing to say so.
        static void AddWindow(Renderer r, bool shopfront)
        {
            Windows.Add(r);
            WindowIsShop.Add(shopfront);
            // NO EMISSION MAP, EVER, AND THE SENTENCE IS EARNED. Three
            // landed builds each killed the glow a different way the theory
            // said was safe: the panes mask through the material slot, the
            // panes mask through this block, and finally BUILT-IN WHITE
            // through this block — night means 0.087, 0.080, 0.075 against
            // 0.130 unbound, the sweep reading zero lit at every multiplier
            // all three times. The scene's own control closed the case: the
            // glow worked for weeks with the slot UNBOUND, and no texture
            // in that slot survives this player's shader set. The lit look
            // therefore rides _EmissionColor alone, and the sash structure
            // lives in the albedo by day and in the per-window SCALE below
            // by night. If somebody re-attempts a mask, it must ship as an
            // imported build-time asset and prove itself on a landed still
            // before anything else stacks on it.
            //
            // The scale: a window smaller than a room burns at full
            // strength — a 1.4m sash glowing whole IS a lit sash. A band
            // wider than that gets a hashed dimming, deterministic in its
            // position, so a wide wall reads as rooms in different states
            // instead of one glowing sheet.
            float scale = 1f;
            var b = r.bounds;
            float across = Mathf.Max(b.size.x, b.size.z);
            if (across > 3f)
            {
                int h = ((int)(b.center.x * 13.7f) * 73856093)
                      ^ ((int)(b.center.z * 13.7f) * 19349663)
                      ^ ((int)(b.center.y * 7.3f) * 83492791);
                scale = 0.35f + 0.55f * (Mathf.Abs(h) % 1000 / 999f);
            }
            WindowGlowScale.Add(scale);
        }

        static Renderer WinBox(string name, Vector3 center, Vector3 size)
        {
            var go = MakeBox(name, center, size, AssetLibrary.Window);
            // NO COLLIDER ON A WINDOW. MakeBox's primitive ships one, and a
            // ground-floor window's box sits at exactly chest height on the
            // face of the wall: shiftTrace's first landing has the courier
            // dead still for 197 consecutive ticks pressed 0.1m against
            // `Bldg69_win_zP_0_0`, running the whole time, nobody near him —
            // the wall-slide rounds the building but not the sill bolted to
            // it. The mass's own collider is centimetres behind, so nothing
            // walks through a wall; sight rays and shot probes hit the wall
            // instead of the glass, the same answer a street away.
            Object.Destroy(go.GetComponent<Collider>());
            // ONE TEXTURE REPEAT IS ONE SASH (a 2x2 of panes, drawn and
            // emission-masked by the same predicate). INTEGER repeats, so
            // every band edge lands on a frame instead of cutting a pane
            // mid-glass: a 1.4m near window gets one sash, a nine-metre far
            // band gets six — which is what turns the wall-of-light slabs
            // into rows of windows at zero geometry cost. Written before
            // the glow sweeps ever run, and both they and SetTiling are
            // read-modify-write on the same property block, so neither
            // stomps the other (checked at all three writers, 22 Aug).
            float across = Mathf.Max(size.x, size.z);
            SetTiling(go, Mathf.Max(1f, Mathf.Round(across / 1.5f)),
                          Mathf.Max(1f, Mathf.Round(size.y / 1.4f)));
            return go.GetComponent<Renderer>();
        }

        /// The uncle's bar: an open-fronted room in the NW building's corner.
        static void BuildBar()
        {
            MakeBox("Bar_Floor", new Vector3(-8.5f, 0.05f, 8.5f), new Vector3(7, 0.1f, 7), AssetLibrary.Wood);
            MakeBox("Bar_WallN", new Vector3(-8.5f, 1.75f, 12f), new Vector3(7, 3.5f, 0.3f), AssetLibrary.Plaster);
            MakeBox("Bar_WallW", new Vector3(-12f, 1.75f, 8.5f), new Vector3(0.3f, 3.5f, 7), AssetLibrary.Plaster);
            MakeBox("Bar_WallE", new Vector3(-5f, 1.75f, 10.25f), new Vector3(0.3f, 3.5f, 3.5f), AssetLibrary.Plaster);
            MakeBox("Bar_Roof", new Vector3(-8.5f, 3.6f, 8.5f), new Vector3(7.4f, 0.2f, 7.4f), AssetLibrary.Roof);
            MakeBox("Bar_Counter", new Vector3(-8.5f, 0.55f, 7.2f), new Vector3(4.5f, 1.1f, 0.7f), AssetLibrary.Wood);
            MakeBox("Bar_CounterTop", new Vector3(-8.5f, 1.13f, 7.2f), new Vector3(4.7f, 0.08f, 0.9f), AssetLibrary.Metal);

            // Back-bar shelves against the north wall, with a row of bottles on each.
            for (int shelf = 0; shelf < 2; shelf++)
            {
                float sy = 1.5f + shelf * 0.75f;
                MakeBox($"Bar_Shelf{shelf}", new Vector3(-8.5f, sy, 11.6f), new Vector3(5f, 0.08f, 0.5f), AssetLibrary.Wood);
                for (int b = 0; b < 12; b++)
                {
                    int hsh = (shelf * 31 + b * 17) & 7;
                    float h = 0.28f + hsh * 0.03f;
                    float bx = -10.7f + b * 0.4f;
                    MakeBox($"Bar_Bottle{shelf}_{b}", new Vector3(bx, sy + 0.04f + h / 2f, 11.6f), new Vector3(0.12f, h, 0.12f), AssetLibrary.Glass);
                }
            }

            // Stools along the customer side of the counter.
            for (int s = 0; s < 3; s++)
            {
                float sx = -9.7f + s * 1.2f;
                MakeBox($"Bar_StoolLeg{s}", new Vector3(sx, 0.28f, 6.5f), new Vector3(0.1f, 0.56f, 0.1f), AssetLibrary.Metal);
                MakeBox($"Bar_StoolSeat{s}", new Vector3(sx, 0.6f, 6.5f), new Vector3(0.42f, 0.1f, 0.42f), AssetLibrary.Wood);
            }

            // Hanging sign by the door — an emissive panel that lights up at night.
            MakeBox("Bar_SignBracket", new Vector3(-6f, 2.9f, 5.4f), new Vector3(0.08f, 0.5f, 0.5f), AssetLibrary.Metal);
            // A dark frame behind the panel, thinner in X so the glowing
            // faces protrude past it. Without this the sign is a bare
            // emissive BOX: at night its bracket vanishes and from across
            // the plaza it read as a glowing cube floating over the ground
            // (day2_night, first grade-iteration run). A 3cm dark rim is
            // the difference between a mounted sign and a rendering error.
            MakeBox("Bar_SignFrame", new Vector3(-6f, 2.6f, 5.1f), new Vector3(0.06f, 0.8f, 1.7f), AssetLibrary.Metal);
            // THE BAR'S SIGN IS A SHOPFRONT, and it is the one the player
            // navigates by. It keeps late hours by the same rule as any other —
            // which is right: a pub sign that went dark at seven would be a
            // pub that shut before the game's evening starts.
            AddWindow(WinBox("Bar_Sign", new Vector3(-6f, 2.6f, 5.1f), new Vector3(0.1f, 0.7f, 1.6f)),
                      shopfront: true);

            var barLightGo = new GameObject("Bar_Light");
            barLightGo.transform.position = new Vector3(-8.5f, 3.0f, 8.5f);
            var barLight = barLightGo.AddComponent<Light>();
            barLight.type = LightType.Point;
            barLight.range = 9;
            barLight.intensity = 1.1f;
            barLight.color = new Color(1f, 0.85f, 0.6f);
        }

        static void BuildProps()
        {
            // Crate stack outside the bar. "crate_stack" named a prop that
            // never existed (kitAlbedo's full listing found it, with the
            // benches and bins) — the real crates are `base_mesh_wooden_
            // crate_01/02`, stacked here the same way the fallback boxes
            // were, and the boxes remain the fallback on a miss.
            // Probe with the first crate: if it lands the family exists and
            // the rest follow; only a full miss falls back, so a partial
            // landing can never stack primitive boxes on real crates.
            var crate0 = AssetLibrary.TryInstantiateProp("base_mesh_wooden_crate_01",
                new Vector3(4.2f, 0f, 9f), Quaternion.identity);
            bool crates = crate0 != null;
            if (crates)
            {
                TintFurniture(crate0, FurnitureWood);
                TintFurniture(AssetLibrary.TryInstantiateProp("base_mesh_wooden_crate_02",
                    new Vector3(4.9f, 0f, 9.6f), Quaternion.Euler(0, 35f, 0)), FurnitureWood);
                TintFurniture(AssetLibrary.TryInstantiateProp("base_mesh_wooden_crate_01",
                    new Vector3(4.5f, 0.82f, 9.3f), Quaternion.Euler(0, 70f, 0)), FurnitureWood);
            }
            if (!crates)
            {
                MakeBox("Crate_1", new Vector3(4.2f, 0.4f, 9f), Vector3.one * 0.8f, AssetLibrary.Wood);
                MakeBox("Crate_2", new Vector3(4.9f, 0.4f, 9.6f), Vector3.one * 0.8f, AssetLibrary.Wood);
                MakeBox("Crate_3", new Vector3(4.5f, 1.2f, 9.3f), Vector3.one * 0.8f, AssetLibrary.Wood);
            }

            // Street furniture along the arms so the walks read lived-in, not empty.
            Bench(new Vector3(10f, 0, 4.7f));        // market corner
            Bench(new Vector3(-4.7f, 0, 12f), true); // across from the bar
            Bench(new Vector3(4.7f, 0, -12f), true);
            // A dumpster in the alley mouth near the docks corner.
            MakeBox("Dumpster", new Vector3(16f, 0.65f, 4.8f), new Vector3(2.2f, 1.3f, 1.1f), AssetLibrary.Metal);
            MakeBox("Dumpster_Lid", new Vector3(16f, 1.34f, 4.8f), new Vector3(2.3f, 0.08f, 1.2f), AssetLibrary.Metal);

            // A canopy over the bar's open front — marks the door from down the street.
            MakeBox("Bar_Canopy", new Vector3(-6.6f, 3.35f, 5.6f), new Vector3(3.4f, 0.12f, 1.6f), AssetLibrary.Roof);

            // TOWN-PLAN.MD T2 item 6, the red pieces. The phone box stands AT
            // the letter-writer's stall — the exchange's one genuinely
            // outdoor line — so the box the player sees is a phone that
            // works in the fiction, not a prop pretending. The pillar boxes
            // take two corners the founding streets already made busy.
            if (TownPlanEnabled)
            {
                var stall = Ledger.Core.HookMap.Get("letter_stall");
                if (stall != null)
                {
                    var at = new Vector3((float)stall.X + 2.2f, 0, (float)stall.Z - 1.4f);
                    if (PointClear(at, 0.6f)) PhoneBox(at);
                }
                PostBox(new Vector3(11.6f, 0, 5.2f));     // beside the market bench
                PostBox(new Vector3(-20.9f, 0, 13.5f));   // the teahouse kerb
            }
        }

        /// How many cars are parked on kerbs, for the done line — "the
        /// pipeline exists" and "a car stood at a kerb" are different facts.
        public static int ParkedCars;

        /// Where the zebras are, so the parked cars keep clear of them.
        static readonly List<Vector3> ZebraSpots = new List<Vector3>();

        /// How many shop fasciae carry a painted name, same reasoning.
        public static int ShopNamesPainted;

        /// Trade names for the fasciae (town-plan T2). Late-analog British
        /// port: surnames and trades, a few of them from the communities the
        /// design doc gives the market quarter. Deliberately NOT the names
        /// of any cast member — a shop sign that matches a witness's surname
        /// would tell the player a fact the sim does not know it is telling.
        static readonly string[] ShopNames =
        {
            "HODGSON'S GROCERS", "MARLOW BUTCHERS", "BLYTHE & SON BAKERS",
            "TIDE & ANCHOR CAFE", "CALLOWAY HARDWARE", "P. QUINN NEWSAGENT",
            "REGENT DRY CLEANING", "HARBOUR FISH BAR", "STANNARD CHEMIST",
            "KOWALSKI TAILOR", "OSMAN GENERAL STORE", "CROWN LAUNDERETTE",
            "FERRIER SHOE REPAIRS", "NG'S KITCHEN", "VARGA WATCH & CLOCK",
            "DELVE & DAUGHTERS", "BECKETT TOBACCONIST", "ROPER'S IRONMONGERY",
        };
        static readonly string[] WarehouseNames =
        {
            "BONDED STORE No.4", "ALBION ROPEWORKS", "MERSEA IMPORT CO.",
            "GRAINGER & CO. SHIPPING", "NORTH QUAY COLD STORE", "IRONSIDE FORWARDING",
        };

        /// Weathered canvas, not carnival: the dark end of seaside stripes.
        static readonly Color[] AwningPaints =
        {
            new Color(0.30f, 0.24f, 0.20f),   // faded tan
            new Color(0.18f, 0.26f, 0.24f),   // sea green
            new Color(0.30f, 0.16f, 0.16f),   // oxblood
            new Color(0.20f, 0.22f, 0.30f),   // washed navy
        };

        /// The same vocabulary at JOINERY values — gloss-painted wood reads
        /// a step and a half brighter than canvas. Sized from the census
        /// arithmetic: these display ~0.3-0.4, so the 39% of the dark band
        /// they cover should carry the left-third median visibly without
        /// reading as fresh paint (the ladder judges the landing).
        static readonly Color[] ShopfrontPaints =
        {
            new Color(0.48f, 0.39f, 0.32f),   // tan, gloss-worn
            new Color(0.30f, 0.43f, 0.39f),   // sea green
            new Color(0.47f, 0.27f, 0.26f),   // oxblood
            new Color(0.33f, 0.36f, 0.48f),   // washed navy
        };

        /// TOWN-PLAN.MD T2 item 7: parked cars, the cheapest lived-in signal
        /// there is. Deterministic kerb slots along driveable street edges,
        /// HALF-ON-KERB as a British terrace street actually parks (an 8m
        /// carriageway does not spare a full parking lane), filled ~55% with
        /// kit saloons in the town paints — GameController.KitPaints (the
        /// table lives in TrafficHost.cs, which declares no type of its own
        /// name), one palette for every car in town. Each car joins Masses
        /// so walkers
        /// route around a bonnet instead of through it; `massInRoad` is
        /// untouched (it reads StreetMap's own registry, not this list).
        ///
        /// The mesh normalisation is a deliberate small twin of
        /// TrafficHost.EnsureBody's — scale by longest horizontal axis,
        /// yaw 90 if X-long, seat by bounds — kept separate because that
        /// path is proven on a moving fleet mid-playtest-week and a shared
        /// refactor now risks both for tidiness.
        static void BuildParkedCars()
        {
            ParkedCars = 0;
            if (!TownPlanEnabled) return;
            string[] stems = { "sedan", "suv", "hatchback_sports", "sedan_sports", "van" };
            foreach (var e in Ledger.Core.StreetMap.Edges)
            {
                if (!e.Driveable || e.Kind == "lane" || e.Length < 26) continue;
                var a = Ledger.Core.StreetMap.Node(e.A);
                var b = Ledger.Core.StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                // A goods yard keeps its vehicles inside its gates.
                if (Ledger.Core.StreetMap.DistrictAt((a.X + b.X) / 2, (a.Z + b.Z) / 2) == "Ironside")
                    continue;

                int h = StableHash(e.A) * 31 + StableHash(e.B);
                var rng = new System.Random(7331 + (h & 0x7fffffff) % 100000);
                float dx = (float)(b.X - a.X), dz = (float)(b.Z - a.Z);
                float len = Mathf.Sqrt(dx * dx + dz * dz);
                dx /= len; dz /= len;
                bool alongZ = Mathf.Abs(dz) > Mathf.Abs(dx);
                float side = (h & 1) == 0 ? 1f : -1f;
                var perp = new Vector3(-dz, 0, dx) * side;
                float kerb = (float)e.Width / 2f;

                for (float s = 9f; s < len - 9f; s += 6.5f)
                {
                    if (rng.NextDouble() > 0.55) continue;
                    var p = new Vector3((float)a.X + dx * s, 0, (float)a.Z + dz * s) + perp * kerb;
                    if (!PointClear(p, 0.3f)) continue;
                    // Not on a zebra: a car parked across a crossing is worse
                    // grammar than having no crossing at all.
                    bool onZebra = false;
                    foreach (var z in ZebraSpots)
                        if ((z - p).sqrMagnitude < 4.5f * 4.5f) { onZebra = true; break; }
                    if (onZebra) continue;
                    float yaw = Mathf.Atan2(dx, dz) * Mathf.Rad2Deg + (side > 0 ? 0f : 180f);
                    ParkedCar(p, yaw, stems[rng.Next(rng.NextDouble() < 0.8 ? 4 : 5)],
                        GameController.KitPaints[rng.Next(GameController.KitPaints.Length)]);
                    Masses.Add((p, alongZ ? new Vector3(1.8f, 1.5f, 4.3f)
                                          : new Vector3(4.3f, 1.5f, 1.8f)));
                    ParkedCars++;
                }
            }
        }

        static void ParkedCar(Vector3 p, float yaw, string stem, Color paint)
        {
            float targetLen = stem == "van" ? 4.6f : 4.1f;
            var kit = AssetLibrary.TryInstantiateProp("car_kit_" + stem, p,
                Quaternion.Euler(0, yaw, 0));
            if (kit != null)
            {
                var rends = kit.GetComponentsInChildren<Renderer>();
                if (rends.Length == 0) { Object.Destroy(kit); }
                else
                {
                    var bo = rends[0].bounds;
                    foreach (var r in rends) bo.Encapsulate(r.bounds);
                    // Longest horizontal axis is the car's length whatever
                    // the author called forward; X-long means turn it 90.
                    float lx = bo.size.x, lz = bo.size.z;
                    if (lx > lz) kit.transform.Rotate(0, 90f, 0, Space.Self);
                    float longest = Mathf.Max(lx, lz);
                    if (longest > 0.3f) kit.transform.localScale *= targetLen / longest;
                    bo = rends[0].bounds;
                    foreach (var r in rends) bo.Encapsulate(r.bounds);
                    kit.transform.position += Vector3.up * (p.y - bo.min.y);
                    AssetLibrary.PaintKit(rends, paint);
                    foreach (var c in kit.GetComponentsInChildren<Collider>())
                        Object.Destroy(c);
                    return;
                }
            }
            // Fallback: two boxes that read as a car at street distance.
            var body = Tint(MakeBox($"Parked_{ParkedCars}_body", p + new Vector3(0, 0.62f, 0),
                new Vector3(1.7f, 1.0f, 4.0f), AssetLibrary.Metal), paint);
            body.transform.rotation = Quaternion.Euler(0, yaw, 0);
            var cabin = Tint(MakeBox($"Parked_{ParkedCars}_cabin", p + new Vector3(0, 1.28f, 0),
                new Vector3(1.5f, 0.55f, 2.2f), AssetLibrary.Metal), paint);
            cabin.transform.rotation = Quaternion.Euler(0, yaw, 0);
        }

        static int StableHash(string s)
        {
            int hh = 17;
            foreach (var ch in s) hh = hh * 31 + ch;
            return hh;
        }

        /// Chimneys that smoke, and how many do. TOWN-PLAN.MD T4: "a frame
        /// with a dozen moving things reads alive", and smoke is the
        /// cheapest of the dozen. A SUBSET smokes — every ninth stack —
        /// because forty emitters is atmosphere and seven hundred is a
        /// house fire, and the CI software rasteriser pays per pixel of
        /// overdraw. Deterministic pick, so the same stacks smoke in every
        /// still. Fails closed on a missing shader, like every effect here.
        public static int SmokeStacks;

        static void BuildSmoke()
        {
            SmokeStacks = 0;
            if (!TownPlanEnabled) return;
            var shader = Shader.Find("Hidden/LedgerSmoke");
            if (shader == null) return;

            // One soft radial sprite, shared by every emitter.
            var tex = new Texture2D(64, 64, TextureFormat.RGBA32, true, true);
            var px = new Color32[64 * 64];
            for (int y = 0; y < 64; y++)
                for (int x = 0; x < 64; x++)
                {
                    float d = Mathf.Sqrt((x - 31.5f) * (x - 31.5f) + (y - 31.5f) * (y - 31.5f)) / 30f;
                    byte a = (byte)(255 * Mathf.Clamp01(1f - d) * Mathf.Clamp01(1f - d));
                    px[y * 64 + x] = new Color32(255, 255, 255, a);
                }
            tex.SetPixels32(px); tex.Apply(true);
            var smokeMat = new Material(shader) { mainTexture = tex };

            int i = 0;
            // Aim at ~40 smokers and take EVERY stack when there are fewer:
            // the every-ninth rule assumed the hundreds of chimneys the tiny
            // blocks turned out not to hold, and sampled nineteen down to two.
            int step = Mathf.Max(1, TerraceChimneys.Count / 40);
            foreach (var (cpos, baseY) in TerraceChimneys)
            {
                if (i++ % step != 0) continue;
                var go = new GameObject($"Smoke_{SmokeStacks}");
                go.transform.position = cpos + new Vector3(0, baseY + 1.5f, 0);
                var ps = go.AddComponent<ParticleSystem>();
                var main = ps.main;
                // SLOW AND CROWDED WAS THE BUG. At 0.3-0.55 m/s over a 5-8s
                // life from a 0.16m cone, eight-plus sprites sat on top of
                // each other within a metre and their alpha compounded into
                // a SOLID WHITE PILL — five or six of them stood at kerb
                // height in `review_day1_noon` on 57f3d5d and I read them as
                // geometry twice. Rise faster, live shorter, start bigger and
                // fainter, and the same emitter reads as a wisp.
                main.startLifetime = new ParticleSystem.MinMaxCurve(3.5f, 5.5f);
                main.startSpeed = new ParticleSystem.MinMaxCurve(0.9f, 1.4f);
                main.startSize = new ParticleSystem.MinMaxCurve(0.9f, 1.6f);
                // Darker, because a coal-era chimney at noon is a grey smudge
                // against the sky and 0.58 grey reads white on a bright one.
                main.startColor = new Color(0.42f, 0.42f, 0.45f, 0.16f);
                main.maxParticles = 6;
                main.simulationSpace = ParticleSystemSimulationSpace.World;
                var em = ps.emission;
                em.rateOverTime = 0.7f;   // half as many, twice as far apart
                var shape = ps.shape;
                shape.shapeType = ParticleSystemShapeType.Cone;
                shape.angle = 10f;
                shape.radius = 0.35f;   // spread at birth, so they cannot stack
                // The prevailing wind, one direction for the whole town —
                // smoke that disagrees with itself reads as a bug.
                var vel = ps.velocityOverLifetime;
                vel.enabled = true;
                vel.x = 0.4f; vel.z = 0.18f;
                var col = ps.colorOverLifetime;
                col.enabled = true;
                var g = new Gradient();
                g.SetKeys(
                    new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                    new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(0.42f, 0.2f),
                            new GradientAlphaKey(0f, 1f) });
                col.color = new ParticleSystem.MinMaxGradient(g);
                var sol = ps.sizeOverLifetime;
                sol.enabled = true;
                sol.size = new ParticleSystem.MinMaxCurve(1f,
                    new AnimationCurve(new Keyframe(0f, 0.4f), new Keyframe(1f, 1.6f)));
                var rend = go.GetComponent<ParticleSystemRenderer>();
                rend.sharedMaterial = smokeMat;
                SmokeStacks++;
            }
        }

        /// Gulls over the docks (town-plan T4). A handful of white shapes
        /// on slow circles above Ironside and the quay line — the second
        /// cheapest motion there is, and the one that says PORT from any
        /// street in town. GullHost drives them all from one Update.
        public static int Gulls;

        static void BuildGulls()
        {
            Gulls = 0;
            if (!TownPlanEnabled) return;
            var host = new GameObject("Gulls").AddComponent<GullHost>();
            Gulls = host.Build();
        }

        /// A K6 in boxes: red shell, domed cap in two steps, dark glazing on
        /// three sides with horizontal bars, a pale sign band under the cap.
        /// The fourth side is the door and stays solid — nobody models a
        /// hinge for a silhouette. Red is a property-block multiply over the
        /// plaster base, the same trick the vehicles use for their paint.
        static void PhoneBox(Vector3 at)
        {
            var red = new Color(0.62f, 0.07f, 0.07f);
            Tint(MakeBox("PhoneBox_plinth", at + new Vector3(0, 0.05f, 0),
                new Vector3(1.05f, 0.1f, 1.05f), AssetLibrary.Concrete), Color.white);
            MakeBoxCol("PhoneBox_body", at + new Vector3(0, 1.25f, 0),
                new Vector3(0.92f, 2.3f, 0.92f), red);
            MakeBoxCol("PhoneBox_cap", at + new Vector3(0, 2.46f, 0),
                new Vector3(1.0f, 0.12f, 1.0f), red);
            MakeBoxCol("PhoneBox_dome", at + new Vector3(0, 2.58f, 0),
                new Vector3(0.8f, 0.12f, 0.8f), red);
            var glass = new Color(0.16f, 0.19f, 0.22f);
            foreach (var (dx, dz, sx, sz, k) in new[] {
                (0.47f, 0f, 0.02f, 0.66f, 0), (-0.47f, 0f, 0.02f, 0.66f, 1), (0f, 0.47f, 0.66f, 0.02f, 2) })
            {
                Tint(MakeBox($"PhoneBox_glass_{k}", at + new Vector3(dx, 1.35f, dz),
                    new Vector3(sx, 1.5f, sz), AssetLibrary.Metal), glass);
                for (int b = 0; b < 3; b++)
                    Tint(MakeBox($"PhoneBox_bar_{k}_{b}", at + new Vector3(dx, 0.85f + b * 0.5f, dz),
                        new Vector3(sx + 0.02f, 0.05f, sz + 0.02f), AssetLibrary.Plaster), red);
                Tint(MakeBox($"PhoneBox_sign_{k}", at + new Vector3(dx, 2.25f, dz),
                    new Vector3(sx + 0.01f, 0.18f, sz + 0.01f), AssetLibrary.Plaster),
                    new Color(0.9f, 0.88f, 0.8f));
            }
        }

        /// A pillar box: red drum on a plinth, black cap line, dark slot.
        static void PostBox(Vector3 at)
        {
            if (!PointClear(at, 0.4f)) return;
            var red = new Color(0.62f, 0.07f, 0.07f);
            Tint(MakeBox("PostBox_plinth", at + new Vector3(0, 0.04f, 0),
                new Vector3(0.62f, 0.08f, 0.62f), AssetLibrary.Concrete), Color.white);
            var drum = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            drum.name = "PostBox_drum";
            drum.transform.position = at + new Vector3(0, 0.62f, 0);
            drum.transform.localScale = new Vector3(0.48f, 0.55f, 0.48f);
            // A REAL RED MATERIAL, NOT A TINT OVER PLASTER. Two tall white
            // objects stand in `review_day1_noon` and there are exactly two
            // pillar boxes in the city — the drum is 0.48 by 1.1m and so are
            // they. The property-block multiply is not reaching this
            // renderer, and rather than spend another build finding out why,
            // the colour moves into the material itself: `Opaque` is a
            // shared cached material per colour, so it costs no draw call
            // and cannot be silently overwritten by a later property block.
            drum.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Opaque(red);
            Object.Destroy(drum.GetComponent<Collider>());
            var cap = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            cap.name = "PostBox_cap";
            cap.transform.position = at + new Vector3(0, 1.2f, 0);
            cap.transform.localScale = new Vector3(0.52f, 0.05f, 0.52f);
            cap.GetComponent<Renderer>().sharedMaterial =
                AssetLibrary.Opaque(new Color(0.12f, 0.12f, 0.13f));
            Object.Destroy(cap.GetComponent<Collider>());
            Tint(MakeBox("PostBox_slot", at + new Vector3(0, 0.98f, 0.23f),
                new Vector3(0.3f, 0.05f, 0.04f), AssetLibrary.Metal),
                new Color(0.1f, 0.1f, 0.1f));
        }

        /// WHAT IS DRAWING UNITY'S DEFAULT WHITE, and what it is called.
        ///
        /// `review_day1_noon` on 7466829 has five or six featureless white
        /// pills standing at the kerb. `walkersPrimitive=0 of 49` rules out
        /// the one thing this project already instruments — a walker still
        /// wearing its spawn capsule — so it is scenery, and every candidate
        /// is something added this weekend.
        ///
        /// GENERAL RATHER THAN A GUESS. I could name three suspects and test
        /// them one build at a time; `CreatePrimitive` hands out
        /// `Default-Material` to anything nobody dressed, so ASKING THE SCENE
        /// which renderers still wear it answers the question for every
        /// suspect at once and keeps answering it for whatever gets added
        /// next. That is the shape `walkersPrimitiveWho` already proved: the
        /// count sends you nowhere, the names send you to the object.
        public static int UndressedRenderers;
        public static string UndressedWho = "none";
        public static int CapsuleMeshes;
        public static string CapsuleWho = "none";

        public static void AuditUndressed()
        {
            int n = 0;
            var names = new List<string>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                var m = r.sharedMaterial;
                if (m != null && m.name != "Default-Material") continue;
                n++;
                if (names.Count < 8) names.Add(r.gameObject.name);
            }
            UndressedRenderers = n;
            UndressedWho = names.Count > 0 ? string.Join("/", names) : "none";
            Debug.Log($"WorldBuilder: undressed renderers {n} [{UndressedWho}]");

            // AND THE CAPSULES, BY NAME AND PLACE. `undressed=0` came back on
            // the first run of the sweep above, so the white pills at the
            // kerb wear a REAL material — a pale one — and "which object is
            // that" is still unanswered. A capsule is not a shape this city
            // builds on purpose anywhere except a walker's spawn husk, so
            // every one of them is worth naming, and the position turns a
            // name into a place I can look at in the next still.
            int caps = 0;
            var capNames = new List<string>();
            foreach (var mf in Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None))
            {
                if (mf.sharedMesh == null || mf.sharedMesh.name != "Capsule") continue;
                caps++;
                if (capNames.Count < 8)
                {
                    var p = mf.transform.position;
                    capNames.Add($"{mf.gameObject.name}@{p.x:0}/{p.z:0}");
                }
            }
            CapsuleMeshes = caps;
            CapsuleWho = capNames.Count > 0 ? string.Join("/", capNames) : "none";
            Debug.Log($"WorldBuilder: capsule meshes {caps} [{CapsuleWho}]");
        }

        /// Property-block colour multiply — one shared material, per-object
        /// colour, no draw-call split. The vehicles' paint trick, reused.
        /// Public: StreetFurniture paints its no-entry discs with it.
        public static GameObject Tint(GameObject go, Color c)
        {
            var r = go.GetComponent<Renderer>();
            var mpb = new MaterialPropertyBlock();
            r.GetPropertyBlock(mpb);
            mpb.SetColor("_Color", c);
            r.SetPropertyBlock(mpb);
            return go;
        }

        /// KIT FURNITURE SHIPS WHITE AND UNTEXTURED. The run the benches,
        /// bins and crates first landed, `kitAlbedo` read every one of them
        /// at 1.00 against walls at 0.15, and the noon still showed the
        /// crate stack glowing in the foreground — the skyline fault, one
        /// street closer. Same repair, same mechanism (the skyline's MPB
        /// tint), and tinted to agree with each prop's own FALLBACK surface
        /// — the boxes these replaced were Wood and Metal — rather than to
        /// an invented colour. Counted so the repaint cannot silently stop.
        public static int FurnitureRepainted;
        // Public because Furniture.cs is the SECOND placer of these props —
        // found by a white swing bin standing in the road through a repaint
        // that moved 116 renderer sets: one idea, two implementations, and
        // the one nobody looked at was the one missing the line.
        public static void TintFurniture(GameObject go, Color c)
        {
            if (go == null) return;
            // MATERIAL REPLACEMENT, NOT AN MPB TINT — the first version set
            // `_Color` through a property block and `furnitureRepainted=116`
            // landed beside a crate stack exactly as white as before: the
            // base-mesh props import through glTFast (manifest:
            // com.unity.cloud.gltfast), whose shader has no `_Color` to
            // read, so the counter counted calls while nothing changed — a
            // wiring proof that proved the CALL, not the EFFECT. These
            // props are untextured (notex=1 in every PropPrefab line), so
            // swapping to the palette's own Standard flat material loses
            // nothing and its shader variant ships already (every body
            // wears it). The proof that can't lie is the next still plus
            // the family's kitAlbedo staying measured at instantiate.
            foreach (var rr in go.GetComponentsInChildren<Renderer>(true))
            {
                var mats = rr.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                    mats[i] = AssetLibrary.Opaque(c);
                rr.sharedMaterials = mats;
            }
            FurnitureRepainted++;
        }
        // The fallback surfaces' own tints (SurfaceSpec Wood and Metal).
        // Public for Furniture.cs, so the two placers cannot drift apart
        // on what wood and metal mean.
        public static readonly Color FurnitureWood  = new Color(0.28f, 0.22f, 0.18f);
        public static readonly Color FurnitureMetal = new Color(0.30f, 0.31f, 0.33f);

        static void Bench(Vector3 pos, bool alongZ = false)
        {
            // THE PROVISIONAL NAMES WERE WRONG FOR A WEEK AND NOTHING SAID
            // SO until kitAlbedo's first full listing had no bench in it:
            // the city-kit shipped no furniture, so `city_kit_*_bench`
            // missed on every call and the fallback boxes were the only
            // bench Meridian ever had — while FOUR real benches sat in the
            // build under `base_mesh_*` (rule 6, found by an absence). The
            // real names, hashed by position so streets vary; a miss still
            // falls through to the boxes.
            string[] benches = { "base_mesh_park_bench", "base_mesh_curved_stone_bench",
                                 "base_mesh_ornate_bench", "base_mesh_garden_bench_01" };
            int pick = System.Math.Abs((int)(pos.x * 13.7f + pos.z * 7.3f)) % benches.Length;
            var mesh = AssetLibrary.TryInstantiateProp(benches[pick],
                           pos, Quaternion.Euler(0, alongZ ? 0f : 90f, 0))
                    ?? AssetLibrary.TryInstantiateProp(benches[(pick + 1) % benches.Length],
                           pos, Quaternion.Euler(0, alongZ ? 0f : 90f, 0));
            if (mesh != null) { TintFurniture(mesh, FurnitureWood); return; }

            var seat = alongZ ? new Vector3(0.45f, 0.08f, 1.6f) : new Vector3(1.6f, 0.08f, 0.45f);
            var leg = new Vector3(alongZ ? 0.4f : 0.12f, 0.42f, alongZ ? 0.12f : 0.4f);
            int n = Lamps.Count * 31 + (int)(pos.x * 7 + pos.z * 3);
            MakeBox($"BenchSeat_{n}", pos + new Vector3(0, 0.46f, 0), seat, AssetLibrary.Wood);
            const float off = 0.6f;
            MakeBox($"BenchLegA_{n}", pos + new Vector3(alongZ ? 0 : -off, 0.21f, alongZ ? -off : 0), leg, AssetLibrary.Metal);
            MakeBox($"BenchLegB_{n}", pos + new Vector3(alongZ ? 0 : off, 0.21f, alongZ ? off : 0), leg, AssetLibrary.Metal);
        }

        /// Lamps on the grid. Every junction is lit, and long avenue runs get
        /// a pool part-way along, so a night walk anywhere in the district is
        /// strung with light rather than pitch black between two crossings.
        static void BuildLamps()
        {
            foreach (var j in Ledger.Core.StreetMap.Nodes)
            {
                if (!j.IsJunction) continue;
                float off = (float)Ledger.Core.StreetMap.AvenueWidth / 2f + 1.6f;
                var jc = new Vector3((float)j.X, 0, (float)j.Z);
                var pA = jc + new Vector3(off, 0, off);
                var pB = jc - new Vector3(off, 0, off);
                MakeLamp(pA, jc - pA);
                MakeLamp(pB, jc - pB);
            }
            int ei = 0;
            foreach (var e in Ledger.Core.StreetMap.Edges)
            {
                if (!e.Driveable || e.Length < 20) continue;
                var a = Ledger.Core.StreetMap.Node(e.A);
                var b = Ledger.Core.StreetMap.Node(e.B);
                var mid = new Vector3((float)(a.X + b.X) / 2f, 0, (float)(a.Z + b.Z) / 2f);
                bool alongZ = Mathf.Abs((float)(b.Z - a.Z)) > Mathf.Abs((float)(b.X - a.X));
                // Alternating sides under the plan — a run of lamps all down
                // one kerb is the tell of a loop nobody thought about.
                float side = TownPlanEnabled && (ei++ % 2 == 1) ? -1f : 1f;
                float off = ((float)e.Width / 2f + 1.4f) * side;
                var lampAt = mid + (alongZ ? new Vector3(off, 0, 0) : new Vector3(0, 0, off));
                MakeLamp(lampAt, mid - lampAt);
            }
        }

        /// The Hook district (open-city-spec §3): every planned place in the
        /// HookMap registry gets graybox geometry at its coordinates — a mass
        /// set back from the stop point so schedules land at the door, windows
        /// that light at dusk, and a lamp on the busier corners. The generator
        /// decided what exists; this renders it. A purchased pack later reskins
        /// the same truth.
        static void BuildDistrict()
        {
            string[] facades = { AssetLibrary.BrickGrey, AssetLibrary.Plaster, AssetLibrary.BrickRed, AssetLibrary.Concrete };
            int i = 0;
            foreach (var place in Ledger.Core.HookMap.Places)
            {
                // The mass sits BACK FROM THE STREET into its own block, so the
                // door faces the road it is addressed from. The arithmetic
                // lives in PlaceMassOf, SHARED with ClashesWithAuthored so
                // the terraces carve around exactly the box this draws.
                if (!PlaceMassOf(place, out var pos, out var size)) { i++; continue; }
                var stop = new Vector3((float)place.X, 0, (float)place.Z);
                // Recovered from the two points the helper guarantees are
                // distinct — same vector the old inline computation had.
                var dir = (pos - stop).normalized;

                // IS THIS PLACE'S OWN POINT IN THE ROAD, AND IS ITS FACE?
                //
                // All eight pieces of clutter standing in a carriageway belong
                // to four REGISTERED PLACES — `warehouse_row`, `boarding_house`,
                // `crescent_houses`, `laurel_letting`, two items each — and not
                // one belongs to a block building. That is the whole population
                // of the fault and it points at this line.
                //
                // A block building is inset 2.6m from its block edge, "pavement
                // plus a doorstep", measured from the KERB. A place is pushed
                // `size.z/2 + 2.5` from `stop`, which is an authored map
                // coordinate that knows nothing about where the road is. Two
                // implementations of "how far back does a building sit" and only
                // one of them has ever been told about the street — the shape
                // this project keeps finding in pairs.
                //
                // MEASURED, NOT ASSUMED, AND DELIBERATELY NOT FIXED HERE. The
                // fix moves buildings, which re-baselines `massInRoad`, the
                // places gate and every framing shot, and the last two guesses
                // about this world came from reading half of it. So the run says
                // which places are wrong and by how much, and the move happens
                // once that is on paper. `Dressing.WallOffset` is 0.45, so a
                // face less than that from the carriageway CANNOT have clutter
                // on a pavement, whatever else is true.
                // ROAD AND STREET ARE DIFFERENT QUESTIONS AND A FACADE WANTS THE
                // WIDER ONE. `OnRoad` asks about ways a CAR uses; `OnStreet` is
                // true of the lanes that cross block interiors to reach doors as
                // well. A BIN beside a service lane is a bin beside a service
                // lane — which is why the clutter check asks the narrow question
                // — but a BUILDING FACE inside a lane is a building standing in
                // a right of way, and somebody has to be able to get to the
                // doors behind it. `OnStreet` has sat on the reach ledger since
                // it was written waiting for something that needed the wider
                // question; this is it.
                var face = pos - dir * (size.z / 2f);
                if (Ledger.Core.StreetMap.OnRoad(stop.x, stop.z)) PlaceStopsInRoad++;
                bool faceInRoad = Ledger.Core.StreetMap.OnRoad(face.x, face.z);
                bool faceInStreet = Ledger.Core.StreetMap.OnStreet(face.x, face.z);
                if (faceInRoad)
                {
                    PlaceFacesInRoad++;
                    if (PlaceFacesInRoadWho.Count < 12) PlaceFacesInRoadWho.Add(place.Id);
                }
                // COUNTED SEPARATELY, NOT FOLDED IN. A face in a lane but not on
                // a road is a different fault with a different fix, and adding
                // the two would report a number nobody can act on.
                if (faceInStreet && !faceInRoad) PlaceFacesInLane++;

                // Same position hash as BuildBuildings, same reason — and
                // through the variant+grade pick too, so a registered place
                // is not the one flat-coated building on its street.
                var facade = facades[FacadePick(pos)];
                var body = MakeBoxVaried($"District_{place.Id}", pos + new Vector3(0, size.y / 2f, 0), size, facade, pos);
                PrimaryMasses.Add(body);
                SetTiling(body, Mathf.Max(1, Mathf.RoundToInt(size.x / 3.5f)), Mathf.Max(1, Mathf.RoundToInt(size.y / 3.5f)));
                MakeBox($"District_{place.Id}_roof", pos + new Vector3(0, size.y + 0.12f, 0),
                    new Vector3(size.x + 0.4f, 0.25f, size.z + 0.4f), AssetLibrary.Roof);
                if (place.Kind != "corner")
                {
                    AddWindows($"District_{place.Id}", pos, size);
                    GroundFloor($"District_{place.Id}", pos, size, -dir);
                }
                Masses.Add((pos, size));

                // A doorstep pad marks the schedule stop itself.
                MakeBox($"District_{place.Id}_step", stop + dir * 1.2f + new Vector3(0, 0.08f, 0),
                    new Vector3(2.2f, 0.16f, 2.2f), AssetLibrary.Sidewalk);

                // AND THE CLUTTER. The street-facing wall gets whatever has
                // collected against it — deterministic, so the same bin is in
                // the same doorway on every load.
                DressFacade(place.Id, pos, size, -dir, place.Kind != "corner",
                            ProsperityOf(place.Kind));
                i++;
            }

            // Light the district's busier corners so night rounds read.
            // Each arm aimed at the avenue the lamp serves.
            MakeLamp(new Vector3(-27, 0, -5), new Vector3(1, 0, 0));    // outside the pawnshop
            MakeLamp(new Vector3(-25, 0, 13), new Vector3(-1, 0, 0));   // the teahouse corner
            MakeLamp(new Vector3(29, 0, 17), new Vector3(-1, 0, 0));    // the ferry stop
            MakeLamp(new Vector3(23, 0, -9), new Vector3(1, 0, 0));     // the cab rank
            MakeLamp(new Vector3(-17, 0, 19), new Vector3(0, 0, 1));    // the north tenements
            MakeLamp(new Vector3(-11, 0, -17), new Vector3(0, 0, -1));  // the bakery corner
        }

        /// Dress the street-facing wall of a mass (Core/Dressing).
        ///
        /// Seven districts shared three benches and a dumpster before this,
        /// all hand-placed near the bar — so everything past Hook Street was
        /// bare geometry, which is the loudest signal there is that a place
        /// was generated rather than built.
        /// A generic block front, with no per-place data to read. Neutral on
        /// purpose: there is no district wealth field to consult, and picking
        /// a number that makes one street look poorer than another WOULD be
        /// inventing design rather than expressing it.
        const double StreetFrontProsperity = 0.55;
        /// The back of the same building. Nobody sweeps behind a block, and
        /// this is the one place the difference is real rather than invented.
        const double BackAlleyProsperity = 0.15;

        /// Which way a block building faces the road: away from the centre of
        /// its own block, snapped to the dominant axis so the wall it dresses
        /// is a real flat face rather than a diagonal through a corner.
        static Vector3 OutwardFrom(Vector3 pos)
        {
            var block = Ledger.Core.StreetMap.BlockAt(pos.x, pos.z);
            var away = block != null
                ? new Vector3(pos.x - (float)block.CentreX, 0, pos.z - (float)block.CentreZ)
                : new Vector3(pos.x, 0, pos.z);
            if (away.sqrMagnitude < 0.01f) return Vector3.forward;
            return Mathf.Abs(away.x) >= Mathf.Abs(away.z)
                ? new Vector3(Mathf.Sign(away.x), 0, 0)
                : new Vector3(0, 0, Mathf.Sign(away.z));
        }

        /// How kept-up a frontage is, from the ONE piece of data that
        /// actually exists about it.
        ///
        /// Per-district wealth would be the right input and there is no such
        /// field — StreetMap.District carries a name and its avenues and
        /// nothing about how well the street is doing. Rather than invent
        /// one here, this reads the place's own Kind, which is real: a
        /// landmark is kept up, a corner shelter is not. Noted in the roadmap
        /// as a data gap rather than papered over.
        static double ProsperityOf(string kind) =>
            kind == "landmark" ? 0.70
            : kind == "business" ? 0.50
            : kind == "home" ? 0.35
            : 0.20;

        /// WHERE THE DETAIL IS SPENT (the-gap.md §4, the scope call).
        ///
        /// Seven districts of graybox exist and content volume is the one row
        /// on the comparison table that cannot be closed. Spreading a fixed
        /// budget of detail across seven districts buys seven thin ones; the
        /// strategy doc's answer is to stop building geography and make two
        /// or three of them dense.
        ///
        /// This is that answer, and it is a list of two coordinates. Hook is
        /// the opening district and where the whole first week happens.
        /// Copper Row is the second because it is the one the writing already
        /// leans on. Everything else thins with distance, to a floor rather
        /// than to nothing — a bare street is worse than a sparse one.
        ///
        /// Deliberately NOT a district lookup. A per-district multiplier
        /// puts a seam at every boundary, and a street where clutter stops
        /// dead at a line the player cannot see reads as a bug.
        static readonly (double x, double z)[] DenseCores =
        {
            (0, 0),          // Hook Street and the bar — the first week
            (-120, 95),      // Copper Row
        };

        /// How densely to dress a wall at this position.
        public static double DetailAt(Vector3 p) =>
            Ledger.Core.Dressing.DetailAt(
                Ledger.Core.Dressing.NearestCore(p.x, p.z, DenseCores));


        static void DressFacade(string id, Vector3 centre, Vector3 size, Vector3 outward,
                                bool hasDoor, double prosperity)
        {
            // The wall runs across the outward direction.
            var along = new Vector3(-outward.z, 0, outward.x).normalized;
            float half = (Mathf.Abs(along.x) > 0.5f ? size.x : size.z) * 0.5f;
            var faceCentre = centre + outward * ((Mathf.Abs(outward.x) > 0.5f ? size.x : size.z) * 0.5f);
            var a = faceCentre - along * half;
            var b = faceCentre + along * half;

            bool nearCore = Ledger.Core.Dressing.NearestCore(
                faceCentre.x, faceCentre.z, DenseCores) <= NearCoreMetres;
            if (nearCore) FacadesNear++; else FacadesFar++;

            foreach (var d in Ledger.Core.Dressing.Facade(a.x, a.z, b.x, b.z,
                                                          prosperity, !hasDoor, hasDoor,
                                                          DetailAt(faceCentre)))
            {
                var at = new Vector3((float)d.X, 0, (float)d.Z);
                float sc = (float)d.Scale;

                // IS THIS PIECE OF CLUTTER STANDING IN THE ROAD?
                //
                // MEASURED BEFORE ANYTHING IS MOVED, which is the whole of why
                // this is a counter and not a rejection. Nothing in this
                // project has ever asked the question — the reach ledger's
                // entry for `StreetMap.OnStreet` says so in as many words:
                // "what would actually use it is set-dressing that must not
                // stand in the carriageway; nothing places street-level props
                // through a road test". Refusing placements on a bound nobody
                // has read would be inventing a threshold and could silently
                // delete a third of the street's clutter.
                //
                // `OnRoad` AND NOT `OnStreet`, and the difference is load
                // bearing. `OnStreet` is true of any tarmac including the lanes
                // that cross block interiors to reach doors — a bin beside a
                // service lane is a bin beside a service lane. `OnRoad` asks
                // only about the ways a CAR uses, which is where a bin would
                // actually look wrong and be driven through.
                if (Ledger.Core.StreetMap.OnRoad(at.x, at.z))
                {
                    DressedInRoad++;

                    // MEASURED FIRST, MOVED SECOND, AND THE ORDER WAS THE
                    // POINT. The count landed before this did: 8 of 176 facade
                    // items standing in a carriageway, which is small enough to
                    // fix by nudging and far too small to justify REFUSING a
                    // placement. Refusing on a bound nobody had read could have
                    // deleted a third of the street's clutter on a bad guess —
                    // the ratchet rule 5 is about, and the same shape as the
                    // guard that threw away a corrected clip set for being
                    // smaller than the one it replaced.
                    //
                    // BACK TOWARDS THE WALL, which is the one direction that is
                    // always right here. `outward` is the facade's own normal,
                    // so stepping against it moves the bin from the road onto
                    // the pavement it belongs on and never sideways into a
                    // neighbour's doorway.
                    //
                    // BOUNDED AT THE STEPS BELOW AND COUNTED WHEN IT FAILS. A
                    // loop that pulls until it clears would push a bin through
                    // its own wall on a facade that fronts directly onto the
                    // carriageway, and there is nothing to do about that from
                    // here — the building is in the road, not the bin. Those
                    // are left where they are and counted, because a silent
                    // "fixed" that walked an object into a wall would be worse
                    // than the fault.
                    // A METRE AND A QUARTER CLEARED NOTHING — 0 pulled, 8
                    // stuck — so the bound was the wrong question rather than
                    // the wrong number. Two explanations survive and they want
                    // opposite fixes: either these facades genuinely front onto
                    // the carriageway, in which case no pull can help and the
                    // level is the fault; or the clutter is being placed a long
                    // way off its own wall, in which case the pull is fine and
                    // the placement is not.
                    //
                    // FOUR METRES ANSWERED IT, AND THE ANSWER WAS THAT FOUR
                    // METRES IS NOT A NUDGE. `dressedInRoad=8 dressedPulled=2
                    // dressedStuck=6 dressedWorstPull=3.75` — and the fork
                    // above is decided by a constant that was in the code the
                    // whole time.
                    //
                    // `Dressing.WallOffset` is 0.45. EVERY facade item is
                    // placed exactly that far out from its wall — it is a
                    // constant, not a distribution, so "the clutter is metres
                    // off its own wall" was never possible and half the fork
                    // was dead on arrival. Which means a 3.75m pull walked a
                    // bin 3.3m BEHIND the face plane, through its own wall and
                    // into the building, and `DressedPulled++` reported that as
                    // a success. The bound written to prevent exactly this
                    // ("would push a bin through its own wall", three
                    // paragraphs up) stopped preventing it the moment the reach
                    // was widened, and nothing said so — the number got better
                    // while the world got worse, which is rule 5's ratchet
                    // running in the flattering direction.
                    //
                    // SO THE BOUND IS THE WALL, and it is not a number I chose.
                    // Pulling clutter back to the face it leans on is always
                    // right; pulling it past that face is never right, whatever
                    // the road says. `WallOffset` is where those two meet, so
                    // the reach is exactly `WallOffset` and cannot drift from
                    // the placement it is undoing.
                    //
                    // AND THE ANSWER THIS PRODUCES IS PROBABLY WORSE-LOOKING,
                    // WHICH IS THE POINT. If the eight are in the road at 0.45m
                    // from their walls, then those eight walls front onto the
                    // carriageway and no nudge can help: the building is in the
                    // road, not the bin. `dressedStuck` rising to 8 is that
                    // finding being reported instead of hidden, and it moves
                    // the work to the level where it belongs.
                    const int PullSteps = 4;
                    float pullStep = (float)Ledger.Core.Dressing.WallOffset / PullSteps;
                    var pulled = at;
                    bool cleared = false;
                    for (int step = 0; step < PullSteps; step++)
                    {
                        pulled -= outward * pullStep;
                        if (!Ledger.Core.StreetMap.OnRoad(pulled.x, pulled.z))
                        {
                            cleared = true;
                            break;
                        }
                    }
                    if (cleared)
                    {
                        float used = Vector3.Distance(at, pulled);
                        if (used > DressedWorstPull) DressedWorstPull = used;
                        at = pulled;
                        DressedPulled++;
                    }
                    else
                    {
                        DressedStuckInRoad++;
                        // HOW WIDE THE ROAD IN FRONT OF THIS WALL IS — AND THAT
                        // IS NOT WHAT THIS COMMENT SAID FIRST.
                        //
                        // It claimed to measure "how far into the carriageway
                        // the wall itself is", and the first reading came back
                        // `[2.25 4.25 4.50 6.50 10.00 10.00 10.00 10.00]`. I was
                        // one sentence from writing up four buildings standing
                        // in the middle of a road. They are not: this walks
                        // OUTWARD from the face plane, so it crosses the whole
                        // carriageway, and 10.00 is this probe's own cap being
                        // hit while crossing an eight-metre avenue and carrying
                        // on into a junction. A building correctly placed at a
                        // kerb reads exactly the same.
                        //
                        // AND THEN I READ THE BLOCK DATA AND NOT THE PLACEMENT,
                        // AND GOT THE ANSWER WRONG A SECOND TIME.
                        //
                        // `StreetMap` gives blocks `MinX = avenue + halfWidth`,
                        // so the buildable GROUND begins at the kerb — from
                        // which I concluded, and committed, that there is no
                        // pavement anywhere in the map and all eight items are
                        // in the road by construction. `BuildBlockSpecs` insets
                        // every building by `2.6f`, under a comment reading
                        // "pavement + a doorstep", and the registered places
                        // push back `size.z / 2f + 2.5f`. There is a pavement,
                        // it is about two and a half metres, and clutter at
                        // `WallOffset` 0.45 sits well inside it.
                        //
                        // Rule 3 in its exact words: "when your own analysis
                        // says something is missing, open the file and look." I
                        // opened `StreetMap` and stopped, which is the same
                        // mistake as reading a grep hit and not the function —
                        // and it is the second time today that a claim about
                        // the world came from the wrong half of it.
                        //
                        // SO EIGHT IS A SMALL, SPECIFIC FAULT rather than a
                        // level-wide one, and the question is WHICH facades.
                        // The pub is one — its own corner is measurably 1.5m
                        // inside Hook Street. `dressedStuckOn` names them
                        // instead of leaving me to guess a third time.
                        var probe = at - outward * (float)Ledger.Core.Dressing.WallOffset;
                        float into = 0;
                        for (int step = 0; step < 40; step++)
                        {
                            probe += outward * 0.25f;
                            if (!Ledger.Core.StreetMap.OnRoad(probe.x, probe.z)) break;
                            into += 0.25f;
                        }
                        DressedRoadDepth.Add(into);
                        if (DressedStuckOn.Count < 24) DressedStuckOn.Add(id);
                    }
                }
                switch (d.Kind)
                {
                    case Ledger.Core.Clutter.Bin:
                        // `city_kit_*_trash_can` never existed — the kit has
                        // no furniture — so every bin was the fallback box
                        // while four real bins sat unused in the build (same
                        // find as the benches: kitAlbedo's full listing had
                        // no bin family in it). Real names, hashed for
                        // variety; a miss still falls through to the box.
                        string[] bins = { "base_mesh_outdoor_bin", "base_mesh_mesh_bin",
                                          "base_mesh_swing_bin", "base_mesh_cigarette_bin" };
                        int binPick = System.Math.Abs((int)(at.x * 11.3f + at.z * 5.1f)) % bins.Length;
                        var binGo = AssetLibrary.TryInstantiateProp(bins[binPick], at,
                                        Quaternion.Euler(0, (at.x * 61f) % 360f, 0))
                                 ?? AssetLibrary.TryInstantiateProp(bins[(binPick + 1) % bins.Length], at,
                                        Quaternion.Euler(0, (at.x * 61f) % 360f, 0));
                        if (binGo != null) { TintFurniture(binGo, FurnitureMetal); break; }
                        MakeBox($"Bin_{id}_{at.x:0.0}", at + new Vector3(0, 0.55f * sc, 0),
                            new Vector3(0.75f, 1.1f, 0.7f) * sc, AssetLibrary.Metal);
                        break;
                    case Ledger.Core.Clutter.Drainpipe:
                        // Vertical, hugging the wall, full height of the mass.
                        MakeBox($"Pipe_{id}_{at.x:0.0}", at + new Vector3(0, size.y * 0.5f, 0),
                            new Vector3(0.16f, size.y, 0.16f), AssetLibrary.Metal);
                        break;
                    case Ledger.Core.Clutter.Ground:
                        MakeBox($"Hatch_{id}_{at.x:0.0}", at + new Vector3(0, 0.03f, 0),
                            new Vector3(0.9f * sc, 0.06f, 0.9f * sc), AssetLibrary.Concrete);
                        break;
                    case Ledger.Core.Clutter.Awning:
                        // Canvas, not roof felt — the other half of the
                        // census's 39% mat_roof beside the shopfront
                        // surround. Same palette the kit awnings wear,
                        // hashed the same way; Opaque() because an MPB
                        // colour multiplies onto the dark-baked texture.
                        var awnBox = MakeBox($"Awning_{id}", at + new Vector3(0, 2.9f, 0),
                            new Vector3(2.6f, 0.1f, 1.1f), AssetLibrary.Roof);
                        awnBox.GetComponent<Renderer>().sharedMaterial =
                            AssetLibrary.Opaque(AwningPaints[
                                System.Math.Abs((int)(at.x * 13 + at.z * 5)) % AwningPaints.Length]);
                        break;
                    case Ledger.Core.Clutter.Puddle:
                        // Flat, dark and SMOOTH: a puddle is only a puddle
                        // because it reflects the lamps, which is the whole
                        // reason the wet-surface work exists.
                        var pool = MakeBox($"Puddle_{id}_{at.x:0.0}", at + new Vector3(0, 0.012f, 0),
                            new Vector3(1.5f * sc, 0.024f, 1.1f * sc), AssetLibrary.Asphalt);
                        var pr = pool.GetComponent<Renderer>();
                        var mpb = new MaterialPropertyBlock();
                        pr.GetPropertyBlock(mpb);
                        mpb.SetColor("_Color", new Color(0.06f, 0.07f, 0.08f));
                        pr.SetPropertyBlock(mpb);
                        break;
                }
                Dressed++;
                if (nearCore) DressedNear++; else DressedFar++;
            }
        }

        /// How many pieces of clutter the city put down. Read by the sim, so
        /// "the streets are dressed" is a measured claim rather than a hope.
        public static int Dressed;
        /// How many of those landed on a road a car uses. A count with
        /// `Dressed` beside it as its denominator, because "0 in the road" and
        /// "no dressing was placed at all" are different worlds and read the
        /// same without one.
        public static int DressedInRoad;

        /// AND WHERE THE EIGHT ACTUALLY COME FROM. All of them belong to
        /// registered PLACES, none to a block building, and the two rules for
        /// "how far back does a building sit" are different: a block is inset
        /// 2.6m from its own edge, measured from the kerb; a place is pushed
        /// `size.z/2 + 2.5` from an authored map coordinate that has never been
        /// told where the road is.
        ///
        /// `placeStopsInRoad` is how many of those coordinates are themselves on
        /// a carriageway and `placeFacesInRoad` how many of the resulting FACES
        /// are — which is the one that matters, because `Dressing.WallOffset` is
        /// a constant 0.45 and a face that close to a road cannot put anything
        /// on a pavement.
        public static int PlaceStopsInRoad, PlaceFacesInRoad;

        /// PAVEMENT PLUS A DOORSTEP, named once instead of twice. A block
        /// building was inset by a local `2.6f` with exactly this comment
        /// beside it. Naming it does not fix the fault below — that is data,
        /// not code — but it removes the half of "two implementations" that
        /// was a literal nobody could grep for.
        public const float BlockSetback = 2.6f;

        /// AND THE ANSWER IS THAT NO PLACEMENT RULE CAN FIX IT, MEASURED
        /// LOCALLY AGAINST THE REAL STREET GRAPH RATHER THAN GUESSED.
        ///
        /// The note above proposed pushing a place back until its face clears
        /// the carriageway, and said the move waits until the run says which
        /// places are wrong and by how much. It said so; the answer is that the
        /// move is the wrong fix and the reading that says so was ALREADY ON
        /// THE SAME LINE.
        ///
        /// `placeStopsInRoad=31 placeFacesInRoad=22`. I had been reading the 22
        /// as the fault for three builds. **31 of the 52 planned places have an
        /// authored coordinate standing in a carriageway** — the 22 are the
        /// subset whose building geometry then lands there too. A door cannot
        /// be moved out of the road while the ADDRESS is in the middle of it;
        /// all you can do is walk the building away from the stop the schedules
        /// send people to.
        ///
        /// Three variants were run against `HookMap` and `StreetMap` in a local
        /// probe, no build:
        ///
        ///   push back until the face clears      22 -> 13, 19 places capped
        ///   fix the fallback DIRECTION as well   22 -> 11, 13 capped, median
        ///                                        push 7.75m
        ///   the direction fix on its own         22 -> 22, nothing moved
        ///
        /// The second is the instructive one: it "improves" the headline number
        /// while dragging the median building nearly eight metres off its own
        /// front door, which is worse game than a facade in a road and would
        /// have looked like progress. The third shows the direction is not the
        /// problem either.
        ///
        /// AND THE FALLBACK IS STILL WRONG, which is worth knowing separately:
        /// every one of the 22 has `BlockAt(stop) == null` — the coordinate is
        /// in a road, so it is inside no block — and the fallback then points
        /// the building radially outward from the WORLD ORIGIN. Measured
        /// against the true outward normal, six of the twenty-two are aimed
        /// across the road rather than off it. Fixing that alone changes
        /// nothing today because the stop is the fault, but it is a real bug
        /// waiting under this one.
        ///
        /// So the fix is in `HookMap`: move the 31 stops onto a pavement. That
        /// is authored data, it moves where schedules send people, and it wants
        /// its own change with its own before-and-after frame.
        /// And in a LANE but not a road, which is the wider containment
        /// question `StreetMap.OnStreet` answers and nothing had needed.
        public static int PlaceFacesInLane;
        public static readonly System.Collections.Generic.List<string> PlaceFacesInRoadWho
            = new System.Collections.Generic.List<string>();
        /// Of those, how many were pulled back onto the pavement and how many
        /// could not be. `Stuck` is not a failure of the nudge — it is a facade
        /// that fronts directly onto the carriageway, which is a level fact
        /// this cannot fix and must not paper over by walking an object into a
        /// wall.
        public static int DressedPulled, DressedStuckInRoad;
        /// The furthest any item had to be pulled to clear the carriageway.
        ///
        /// IT ASKED A QUESTION THAT COULD ONLY HAVE ONE ANSWER, and read 3.75
        /// before anybody noticed. The comment said "small means the first
        /// bound was simply short; large means clutter is being placed metres
        /// from its own wall" — but `Dressing.WallOffset` is a CONSTANT 0.45,
        /// so the second case does not exist and a large reading could only
        /// ever mean the pull had walked an object through its own wall. Now
        /// that the reach is bounded at the wall this can never exceed 0.45,
        /// which makes it a check on the bound rather than a fork.
        public static float DressedWorstPull;

        /// FOR EACH ITEM THE WALL COULD NOT SAVE: how deep the carriageway runs
        /// outward from its face plane.
        ///
        /// Once the pull stops at the wall, "stuck" stops being a tuning
        /// question and becomes a level one — the building is in the road. This
        /// is the number that level fix gets sized from, and it is kept as a
        /// series because eight items against a median and a worst are three
        /// different findings: a kerb drawn a few centimetres wide, one facade
        /// standing in a lane, or every wall on a street set back wrong.
        public static readonly List<float> DressedRoadDepth = new List<float>();

        /// WHICH FACADES the stuck clutter belongs to.
        ///
        /// Eight of a hundred and seventy-six, on a street that does have a
        /// two-and-a-half metre pavement — so this is a small specific fault
        /// and the only useful question is which walls. I have now guessed at
        /// it twice, once from a probe that measured the road's width and once
        /// from block data that does not describe where buildings go. A list of
        /// names ends the guessing.
        public static readonly List<string> DressedStuckOn = new List<string>();

        /// Doors built. Counted separately from `Dressed` because a door is
        /// architecture rather than clutter: bins thin out in a far district by
        /// design and an entrance must not, so a floor on the total would say
        /// nothing about whether the buildings can be read as places.
        public static int Doors;

        /// How many of each kind of premises the city built, indexed by
        /// `Dressing.Premises`. Printed because "the buildings vary" is a claim
        /// and a frame at street level sees perhaps six of them — a distribution
        /// is the only way to know whether the whole town varies or just the
        /// corner the camera happens to be on.
        ///
        /// NOT `Premises`, which is what I called it first. `lint-usings`
        /// flagged it: `Ledger.Core.Dressing.Premises` is the enum this counts,
        /// and a field in another assembly wearing the same bare name is
        /// exactly the ambiguity that linter exists to catch. It was a false
        /// positive about the USING and a true one about the NAME.
        public static readonly int[] PremisesBuilt = new int[4];

        /// The same four counts per district. See the note at the increment:
        /// a town-wide total cannot say whether the sheds are in the
        /// industrial quarter or on a residential street, which is the only
        /// question the district table exists to answer.
        public static readonly System.Collections.Generic.Dictionary<string, int[]>
            PremisesByDistrict = new System.Collections.Generic.Dictionary<string, int[]>();

        /// Compact, no spaces — a verdict value may not contain one. Sheds
        /// first in each row because that is the number being watched.
        public static string PremisesByDistrictLine()
        {
            if (PremisesByDistrict.Count == 0) return "none";
            var rows = new System.Collections.Generic.List<string>();
            foreach (var kv in PremisesByDistrict)
                rows.Add($"{kv.Key}:shed{kv.Value[3]}/shop{kv.Value[0]}"
                         + $"/house{kv.Value[1]}/ten{kv.Value[2]}");
            rows.Sort();
            return string.Join(" ", rows).Replace(" ", "|");
        }

        /// PIECES AND FACADES, split by whether they are near a dense core.
        ///
        /// The total alone stopped being the right measurement the moment
        /// detail started concentrating: thinning the far districts LOWERS it
        /// by design, so a floor on the total now fails for the feature
        /// working. What the concentration actually claims is that a wall in
        /// Hook carries more than an identical wall at the edge of the map,
        /// and that is pieces PER FACADE on each side of the ramp.
        public static int DressedNear, DressedFar;
        public static int FacadesNear, FacadesFar;
        /// Within this of a core counts as "in a dense district" for the gate.
        public const double NearCoreMetres = 110;

        public static Light BuildSun()
        {
            var go = new GameObject("Sun");
            var sun = go.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.shadows = LightShadows.Soft;
            // 0.75 → 0.93 (M17.10 V1). At 0.75 a shadowed pixel kept a
            // quarter of the sun ON TOP of the old over-bright ambient, which
            // together is most of why no noon still has ever shown a shadow
            // worth pointing at. The built-in term is lerp(1, map, strength),
            // so what strength leaves behind is DIRECT sun-coloured leak that
            // also desaturates the cool ambient fill inside the shadow —
            // 0.93 leaves 7%, and the research arithmetic through our own
            // tonemap puts the shadowed:lit display ratio near the 0.5 the
            // GTA reference noons read at. Not 1.0: with ambient at 0.45 of
            // the dome there is fill to catch, but a fully-black direct term
            // still risks reading as a hole on dark albedo.
            // 0.93 -> 0.85, AND THE NUMBER IS A PRINTED RUNG.
            //
            // The GTA reference noons put a cast shadow near HALF the lit
            // brightness; ours sat at 0.32. `shadowSeries` walks the strength
            // over a pair found by `FindShadowPair` — a sunlit wall WITH
            // geometry between it and the sun, and an unblocked one beside it
            // for the denominator, both from one sweep:
            //
            //     s0.93 0.043|0.133 = 0.32    s0.65 0.110|0.133 = 0.83
            //     s0.85 0.063|0.133 = 0.47    s0.55 0.125|0.133 = 0.94
            //     s0.75 0.086|0.133 = 0.65
            //
            // 0.85 lands 0.474. No interpolation: it is the rung measured.
            //
            // THE LIT SIDE IS CONSTANT AT 0.133 ACROSS EVERY RUNG, which is
            // what makes this trustworthy — a lever that only touches shadows
            // must not move the denominator, and this one demonstrably does
            // not. Three earlier attempts at this number were read off
            // fixtures where the "shaded" wall was `nSun:0.00`, a face the
            // sun never reaches, whose shade could not respond to anything.
            //
            // AND IT IS THE LEVER THE OTHER TWO ARE NOT. The fill is capped
            // below share 1.0 by a CoreTest defending something true (a wall
            // seeing part of the sky cannot receive the whole of it), and the
            // KEY moves both sides together — `sunSeries` on the same pair
            // holds the ratio at 0.30-0.36 while dimming the whole frame,
            // which is a darker picture and not a better one.
            sun.shadowStrength = 0.85f;
            return sun;
        }

        /// TOWN-PLAN.MD T2 item 6: a lamp with a HEAD. The kit road light is
        /// tried first (curved arm over the carriageway); the two boxes
        /// below are the fallback that shipped every build until now. The
        /// kit mesh's own conventions are not assumed: it is scaled to a
        /// 5.2m head from its measured bounds, ORIENTED by them — the arm
        /// makes the bounds asymmetric about the pivot, and rotating that
        /// offset onto `towardRoad` points the arm at the road whatever
        /// axis the FBX author chose — seated by them, and painted the
        /// near-black green of a British column over the kit palette.
        static void MakeLamp(Vector3 basePos, Vector3? towardRoad = null)
        {
            var kit = TownPlanEnabled
                ? AssetLibrary.TryInstantiateProp("city_kit_roads_light_curved",
                      basePos, Quaternion.identity)
                : null;
            if (kit != null)
            {
                var rends = kit.GetComponentsInChildren<Renderer>();
                if (rends.Length > 0)
                {
                    var b = rends[0].bounds;
                    foreach (var r in rends) b.Encapsulate(r.bounds);
                    if (b.size.y > 0.5f)
                        kit.transform.localScale *= 5.2f / b.size.y;

                    b = rends[0].bounds;
                    foreach (var r in rends) b.Encapsulate(r.bounds);
                    var armOff = b.center - basePos; armOff.y = 0;
                    if (towardRoad.HasValue && armOff.sqrMagnitude > 0.02f)
                    {
                        float have = Mathf.Atan2(armOff.x, armOff.z) * Mathf.Rad2Deg;
                        float want = Mathf.Atan2(towardRoad.Value.x, towardRoad.Value.z) * Mathf.Rad2Deg;
                        kit.transform.rotation = Quaternion.Euler(0, want - have, 0);
                    }
                    b = rends[0].bounds;
                    foreach (var r in rends) b.Encapsulate(r.bounds);
                    kit.transform.position += Vector3.up * (basePos.y - b.min.y);

                    var mpb = new MaterialPropertyBlock();
                    mpb.SetColor("_Color", new Color(0.15f, 0.17f, 0.15f));
                    foreach (var r in rends) r.SetPropertyBlock(mpb);
                    foreach (var c in kit.GetComponentsInChildren<Collider>())
                        Object.Destroy(c);

                    // The head is at the arm's end — about twice as far out
                    // as the bounds centre — up at the top of the mesh.
                    b = rends[0].bounds;
                    foreach (var r in rends) b.Encapsulate(r.bounds);
                    var head = b.center + (b.center - basePos) * 1.0f;
                    var kgo = new GameObject($"LampLight_{Lamps.Count}");
                    kgo.transform.position = new Vector3(head.x, b.max.y - 0.25f, head.z);
                    var klight = kgo.AddComponent<Light>();
                    klight.type = LightType.Point;
                    klight.range = 12;
                    // The kit lamp takes the same linear trim as its
                    // procedural twin below — one ratio, both sites.
                    klight.intensity = 0.95f;
                    klight.color = new Color(1f, 0.82f, 0.55f);
                    klight.enabled = false;
                    LightShaft.Attach(klight, 1.0f);
                    Lamps.Add(klight);
                    return;
                }
                Object.Destroy(kit);
            }

            MakeBox($"LampPole_{Lamps.Count}", basePos + new Vector3(0, 1.75f, 0), new Vector3(0.15f, 3.5f, 0.15f), AssetLibrary.Metal);
            MakeBox($"LampHead_{Lamps.Count}", basePos + new Vector3(0, 3.55f, 0), new Vector3(0.4f, 0.2f, 0.4f), AssetLibrary.Metal);
            var go = new GameObject($"LampLight_{Lamps.Count}");
            go.transform.position = basePos + new Vector3(0, 3.5f, 0);
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 12;
            // 1.4 → 0.95: the linear trim, same reason and ratio as the
            // neon's — see that comment for the measured night floor.
            light.intensity = 0.95f;
            light.color = new Color(1f, 0.82f, 0.55f);
            light.enabled = false;
            LightShaft.Attach(light, 1.0f);
            Lamps.Add(light);
        }

        /// Counts state changes so the simulation can verify the day/night cycle ran.
        public static int LampToggleCount;
        static bool _lampsOn;

        /// SWEPT WHEN SOMETHING CHANGED, NOT EVERY FRAME.
        ///
        /// `UpdateSun` calls this each frame and it walked every lamp in the
        /// city each time, comparing a bool that flips twice a game-day. The
        /// queue's note on the `sun=3.15ms` reading said `UpdateSun` "has no
        /// loops, so it is Unity-side light or shadow work" — it has three,
        /// in the three `WorldBuilder` calls at its end, and this was the one
        /// with no guard on it. (`SetWindowsLit` already had one; `TickNeon`
        /// has to run nightly because it animates.)
        ///
        /// THE COUNT IS PART OF THE KEY, because the city is built
        /// incrementally: a lamp created after the state last changed would
        /// keep whatever `enabled` it was born with if the guard looked only
        /// at the bool. That is the exact way an early-out ships a dark
        /// street at midnight.
        public static void SetLampsEnabled(bool on)
        {
            if (on != _lampsOn) { _lampsOn = on; LampToggleCount++; }
            else if (Lamps.Count == _lampsSweptCount && _lampsSwept) { LampSweepsSkipped++; return; }
            _lampsSwept = true;
            _lampsSweptCount = Lamps.Count;
            LampSweeps++;
            foreach (var lamp in Lamps)
                if (lamp != null && lamp.enabled != on) lamp.enabled = on;
        }
        static bool _lampsSwept;
        static int _lampsSweptCount = -1;
        /// The neon count at which the DAYTIME disable pass last completed;
        /// -1 means it has not, which is also what night sets it back to.
        static int _neonDayDoneAt = -1;
        /// Both halves of each guard, on the done line: a guard that skips
        /// everything and a guard that skips nothing are indistinguishable
        /// from one number (rule 3b). Ratios are what say whether these
        /// bought anything, and they are cumulative, so the done line.
        public static int LampSweeps, LampSweepsSkipped, NeonSweeps, NeonSweepsSkipped;

        /// Make the building windows glow (after dusk) or go dark (daytime). Emission is
        /// driven per-renderer via a property block so all windows keep sharing one
        /// material and one draw-call batch.
        /// How many windows are lit and how many exist. A skyline is a claim
        /// about a city and this is the only number that can check it — and
        /// `WindowsTotal=0` beside a lit night is a build that drew no windows
        /// at all, which every other reading here would report as a dark city.
        public static int WindowsLit { get; private set; }
        public static int WindowsTotal => Windows.Count;
        /// The share of the population that was in when the lights were last
        /// set. Kept so the verdict can print the CAUSE beside the effect: a
        /// third of the windows lit is right at 21:00 and a fault at 04:00, and
        /// nothing but the fraction can say which.
        public static double WindowsHomeFraction { get; private set; } = -1;

        /// EVERY WINDOW WAS THE SAME COLOUR, AND THAT IS THE NIGHT SKYLINE.
        ///
        /// This took a bool and wrote one emissive to every window in seven
        /// districts, so after dusk the city was a wall of identical cream
        /// rectangles — the loudest thing in `review_day1_night` and the first
        /// thing the eye goes to.
        ///
        /// `homeFraction` is measured over the real population every time the
        /// lights change (`Core/Occupancy`), so which windows are lit is not a
        /// decoration: it is how many people are in. Rule 2's shape — the look
        /// decision is which hours a night-circle person is out, which is
        /// authored like the wardrobe's bands; the RESULT is measured and
        /// printed, so a city that goes dark at four is a number rather than a
        /// surprise in a still.
        ///
        /// THE NO-OP GUARD NOW KEYS ON THE FRACTION TOO. It used to return
        /// early whenever `lit` matched the last call, which was right when
        /// there were two states and would have frozen the skyline at whatever
        /// the first evening looked like — a bug that would have shown up as
        /// "the occupancy feature does nothing" with every number saying it ran.
        public static void SetWindowsLit(bool lit, double homeFraction = -1, int hour = -1)
        {
            // Quantised, because the fraction moves continuously with the hour
            // and rewriting every property block on a hairline change is work
            // for no visible difference. A twentieth of the city is about one
            // window in a facade.
            double q = homeFraction < 0 ? -1 : System.Math.Round(homeFraction * 20) / 20.0;
            if (lit == _windowsLit && q == WindowsHomeFraction && hour == _windowsHour
                && Windows.Count > 0) return;
            _windowsLit = lit;
            _windowsHour = hour;
            WindowsHomeFraction = q;
            WindowsLit = 0;
            WindowsShop = WindowsShopLit = 0;
            var mpb = new MaterialPropertyBlock();
            for (int i = 0; i < Windows.Count; i++)
            {
                var win = Windows[i];
                if (win == null) continue;
                // A SHOPFRONT IS NOT SOMEBODY'S FRONT ROOM. Once the flats
                // became a pattern, the two biggest bright objects left in the
                // night frame were ground-floor slabs blazing at ten at night —
                // lit because the flats above them were, having been asked the
                // same question. A shop is lit when it is OPEN.
                bool shop = i < WindowIsShop.Count && WindowIsShop[i];
                if (shop) WindowsShop++;
                bool on = lit && (shop
                    // `hour < 0` means nobody passed one, which is every
                    // existing caller and every test. Those keep the old
                    // behaviour exactly rather than going dark on a default —
                    // a shipped street blacking out because an argument was
                    // omitted is the worst way for this to fail.
                    ? (hour < 0 || Ledger.Core.Occupancy.ShopLit(win.name, hour))
                    : Ledger.Core.Occupancy.WindowLit(win.name, q));
                if (on) { WindowsLit++; if (shop) WindowsShopLit++; }
                win.GetPropertyBlock(mpb);
                float ws = i < WindowGlowScale.Count ? WindowGlowScale[i] : 1f;
                mpb.SetColor("_EmissionColor", on ? WindowLit * ws : WindowDark);
                win.SetPropertyBlock(mpb);
            }
        }

        /// Ground-floor shopfronts, and how many of them are open. Beside the
        /// flats rather than folded into them, because "a third of the windows
        /// are lit" is a completely different finding depending on which third.
        public static int WindowsShop { get; private set; }
        public static int WindowsShopLit { get; private set; }
        static int _windowsHour = -2;

        // ---- primitive helpers ----

        /// TOWN-PLAN.MD T1 item 3, the skyline. Orientation should come free
        /// with a glance down any street: cranes mean the docks (south), the
        /// gasometer marks the goods edge (east). All of it is silhouette
        /// work — fog and distance do the drawing — so every piece is a box
        /// or a cylinder, parked outside the block grid where nothing else
        /// builds: the quay line south of Ironside's last avenue, and the
        /// no-man's strip between Ironside and Gullwing (the goods spur
        /// crosses that strip at z~-127; the drum sits 19m north of it).
        /// How many skyline blocks stood, and how many wore a kit mesh. A
        /// fallback that never fires and one that always fires are the same
        /// single number (rule 3b), and this one has a real chance of never
        /// firing — the models arrive through a fetch job, not through the
        /// repo.
        public static int SkylineBlocks, SkylineKitted;

        /// What the distant towers are painted. See the note at the repaint:
        /// the kit ships its own bright materials and this branch kept them,
        /// so the top third of every wide frame was pale lavender over a noir
        /// street.
        ///
        /// Derived from the landed sky readings rather than picked: noon fog
        /// measures (0.402,0.424,0.446) in the verdict, and something at the
        /// far edge of the map must sit UNDER that or it reads as brighter
        /// than the air in front of it. Slightly blue, because haze is.
        static readonly Color SkylineHaze = new Color(0.34f, 0.36f, 0.40f);

        /// How many kitted towers were repainted, so "the skyline is in the
        /// palette" is a number rather than a hope. Zero with
        /// `skyline=n/m` non-zero would mean the repaint stopped running —
        /// which is exactly how this fault survived in the first place.
        public static int SkylineRepainted;

        /// THE CITY DOES NOT END AT THE LAST TERRACE.
        ///
        /// Every eye-level frame so far ends in blank sky about two hundred
        /// metres out: the street runs to the edge of the built area and then
        /// there is nothing, which is what makes a town read as a diorama
        /// rather than as part of somewhere larger. Jafar's note against GTA5
        /// was density, textures, models — "making it feel like a real city" —
        /// and a horizon is the cheapest third of that.
        ///
        /// USES THE KIT'S LOW-DETAIL BLOCKS, WHICH WERE MEASURED FIRST. The
        /// eleven building models fetched for this decision came back with
        /// every FULL building on a roughly square plan (88x94, 97x94,
        /// 130x103) against our terrace parcels at about 1:2 — so they cannot
        /// be terraces at any scale, and that half of the idea is closed on
        /// geometry. The low-detail set is a different answer: 90 to 112
        /// vertices at a 1:4 tower ratio. Thirty of them is under 4k
        /// vertices, against a scene already carrying ~280k in bodies alone,
        /// and a distant block is exactly where a flat palette colormap costs
        /// nothing — nobody reads brick at three hundred metres.
        ///
        /// SCALED BY THE MESH'S OWN BOUNDS, not by a factor. Kit units are
        /// not metres (its `sedan` measures 150x145x255 and a sedan is 4.2m),
        /// so the height is read off the renderer and scaled to a target the
        /// same way `TrafficHost` fits a car to its kind's length.
        ///
        /// FALLS BACK TO A BOX, and counts which happened. The models arrive
        /// through a fetch job rather than through the repo, so a build
        /// without them is not hypothetical — and a plain tower on the
        /// horizon is still a better horizon than none.
        static void BuildSkyline()
        {
            if (!TownPlanEnabled) return;
            SkylineBlocks = SkylineKitted = SkylineRepainted = 0;

            // The outer ring sits near 112m after the topology stretch and the
            // docks run to z=-174, so this stands well outside both. Two loose
            // rings rather than one so the horizon has depth instead of
            // reading as a fence.
            const int Count = 34;
            string[] models =
            {
                "city-kit-commercial_low-detail-building-a",
                "city-kit-commercial_low-detail-building-b",
                "city-kit-commercial_low-detail-building-c",
            };

            for (int i = 0; i < Count; i++)
            {
                int h = System.Math.Abs(StableHash($"skyline{i}"));
                float ang = (i / (float)Count) * Mathf.PI * 2f
                            + (h % 100) / 100f * 0.09f;          // deterministic jitter
                float radius = 250f + (h / 100 % 7) * 22f + (i % 2 == 0 ? 0f : 46f);

                // SEAWARD STAYS EMPTY. The docks and their cranes are the
                // silhouette on that side and they are the better one; a
                // skyline behind them would read as a city built in the water.
                var dir = new Vector3(Mathf.Sin(ang), 0, Mathf.Cos(ang));
                if (dir.z < -0.55f) continue;

                float target = 26f + (h / 700 % 9) * 6.5f;        // 26..78m
                var at = new Vector3(dir.x * radius, 0, dir.z * radius);

                var kit = AssetLibrary.TryInstantiateProp(
                    models[h % models.Length], at, Quaternion.Euler(0, (h / 7) % 360, 0));
                SkylineBlocks++;
                if (kit != null)
                {
                    SkylineKitted++;
                    kit.name = $"Skyline_{i}";
                    var r = kit.GetComponentInChildren<Renderer>();
                    if (r != null && r.bounds.size.y > 0.01f)
                        kit.transform.localScale = Vector3.one * (target / r.bounds.size.y);
                    // Grounded after scaling — the mesh knows where its feet are.
                    var g = kit.GetComponentInChildren<Renderer>();
                    if (g != null) kit.transform.position = at + Vector3.up * (at.y - g.bounds.min.y);
                    // REPAINTED INTO THE HAZE, BECAUSE THE KIT SHIPS ITS OWN
                    // MATERIALS AND THIS BRANCH WAS KEEPING THEM.
                    //
                    // Found by opening `district_strip`: the top third of the
                    // frame is pale lavender-white towers standing over a noir
                    // brick street. Every building in the town proper goes
                    // through `MakeBoxVaried` and the palette; a kit prop
                    // instantiated here arrives wearing whatever its author
                    // painted it, and nothing touched it.
                    //
                    // THE FIX ALREADY EXISTED ONE SYSTEM OVER. `TrafficHost`
                    // repaints kit cars for exactly this reason — its comment
                    // says the kit's texture is "holiday-brochure mint" and
                    // the first stills had every car on the street wearing it.
                    // Same shape, same cause, and the skyline never got it:
                    // one idea, two implementations, and the one nobody looked
                    // at is the one missing a line.
                    //
                    // NOT AN INVENTED COLOUR (rule 2). The `else` branch four
                    // lines down builds the same tower out of
                    // `AssetLibrary.Concrete`, in the palette, and looks
                    // right. The two branches of one function should produce
                    // one look, so the kit path is tinted to agree with the
                    // fallback rather than to a number somebody chose.
                    //
                    // Darkened further than the near town on purpose: these
                    // stand at the far edge of the map, where distance and
                    // haze take the contrast out of anything real. A skyline
                    // that reads as BRIGHTER than the street in front of it is
                    // the specific thing that made the frame look wrong.
                    //
                    // AND `SkylineRepainted` USED TO BE INCREMENTED ABOVE,
                    // the moment the kit existed and BEFORE the paint was
                    // attempted — so it reported success for something it had
                    // never checked, which is the most misleading form a
                    // counter can take. It counts what the shader ACCEPTED
                    // now. Measured 24 Aug on `district_downtown`: the far
                    // tower is the most saturated thing in the frame (0.469
                    // against brick 0.324 and sky 0.222), and fog cannot
                    // explain it because the fog colour itself sits near
                    // 0.196 — so this repaint may have been evaporating all
                    // along, exactly like the mint saloon's.
                    SkylineRepainted += AssetLibrary.PaintKit(
                        kit.GetComponentsInChildren<Renderer>(), SkylineHaze) > 0 ? 1 : 0;
                    // `Object.Destroy`, not `Destroy` — this class is static
                    // and has no MonoBehaviour to inherit it from. Caught by
                    // the local Game-layer compile pass rather than by a
                    // twenty-eight-minute round trip.
                    foreach (var col in kit.GetComponentsInChildren<Collider>())
                        Object.Destroy(col);
                }
                else
                {
                    float w = 14f + (h / 9 % 5) * 4f;
                    MakeBox($"Skyline_{i}", at + Vector3.up * (target * 0.5f),
                        new Vector3(w, target, w), AssetLibrary.Concrete);
                }
            }
        }

        static void BuildLandmarks()
        {
            if (!TownPlanEnabled) return;

            // Three quay cranes, jibs slewed to different angles so they read
            // as machines parked mid-task rather than one machine copied.
            float[] cxs = { -34f, 2f, 36f };
            float[] slew = { 160f, 200f, 125f };   // yaw; roughly seaward
            for (int i = 0; i < cxs.Length; i++)
            {
                float x = cxs[i], z = -174f;
                // Two stepped sections, not one thin post: at review distance
                // a 1.4m tower faded to nothing while the 17m jib survived,
                // and the first landed build showed three jibs FLOATING.
                // Thickness is what buys a silhouette its legs.
                MakeBox($"Crane_{i}_tower", new Vector3(x, 5f, z),
                    new Vector3(2.8f, 10f, 2.8f), AssetLibrary.Metal);
                MakeBox($"Crane_{i}_tower_up", new Vector3(x, 14f, z),
                    new Vector3(1.9f, 8f, 1.9f), AssetLibrary.Metal);
                MakeBox($"Crane_{i}_cab", new Vector3(x, 18.7f, z),
                    new Vector3(2.6f, 1.9f, 2.4f), AssetLibrary.Metal);
                var dir = new Vector3(Mathf.Sin(slew[i] * Mathf.Deg2Rad), 0,
                                      Mathf.Cos(slew[i] * Mathf.Deg2Rad));
                // The jib: 17m, raked 24 degrees up from the cab. Centre sits
                // half its horizontal reach out along the slew.
                var jib = MakeBox($"Crane_{i}_jib",
                    new Vector3(x, 21.6f, z) + dir * 7.6f,
                    new Vector3(0.8f, 0.8f, 17f), AssetLibrary.Metal);
                jib.transform.rotation = Quaternion.Euler(-24f, slew[i], 0);
                // Counter-jib and its kentledge block, opposite and low.
                var counter = MakeBox($"Crane_{i}_counter",
                    new Vector3(x, 19.2f, z) - dir * 2.6f,
                    new Vector3(0.7f, 0.7f, 5f), AssetLibrary.Metal);
                counter.transform.rotation = Quaternion.Euler(0, slew[i], 0);
                MakeBox($"Crane_{i}_weight", new Vector3(x, 18.3f, z) - dir * 4.6f,
                    new Vector3(1.6f, 1.4f, 1.2f), AssetLibrary.Concrete);
            }

            // The gasometer: a drum in a guide frame that outlives the drum's
            // travel — the frame runs taller than the bell, as they do.
            var gpos = new Vector3(70f, 0f, -108f);
            var drum = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            drum.name = "Gasometer_drum";
            drum.transform.position = gpos + Vector3.up * 5.5f;
            drum.transform.localScale = new Vector3(9f, 5.5f, 9f);
            drum.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);
            for (int k = 0; k < 8; k++)
            {
                float a = k * 45f * Mathf.Deg2Rad;
                MakeBox($"Gasometer_col_{k}",
                    gpos + new Vector3(Mathf.Sin(a) * 9.6f, 7f, Mathf.Cos(a) * 9.6f),
                    new Vector3(0.4f, 14f, 0.4f), AssetLibrary.Metal);
            }
            var ring = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            ring.name = "Gasometer_ring";
            ring.transform.position = gpos + Vector3.up * 13.8f;
            ring.transform.localScale = new Vector3(9.8f, 0.12f, 9.8f);
            ring.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);
        }

        /// A box in a FLAT COLOUR rather than a logical surface — for the
        /// painted street furniture (pillar box, phone box) whose colour is
        /// the point and whose material must not be a tint that can go
        /// missing. `AssetLibrary.Opaque` caches per colour, so a whole
        /// city's red shares one material and one batch.
        static GameObject MakeBoxCol(string name, Vector3 center, Vector3 size, Color c)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = center;
            go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Opaque(c);
            return go;
        }

        static GameObject MakeBox(string name, Vector3 center, Vector3 size, string material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = center;
            go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(material);
            return go;
        }

        /// A box wearing one of its surface's VARIANTS and one of four albedo
        /// GRADES, both chosen by position. Same determinism as `FacadePick`
        /// and the same argument: a city where every brick wall is the same
        /// photograph at the same brightness reads as repetition once there
        /// are enough walls to compare, and 60 parcels became 376. The grade
        /// story is on `AssetLibrary.FacadeGrades`.
        static GameObject MakeBoxVaried(string name, Vector3 center, Vector3 size,
                                        string material, Vector3 at)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = center;
            go.transform.localScale = size;
            int h = Mathf.Abs(Mathf.RoundToInt(at.x * 7.3f + at.z * 3.1f));
            go.GetComponent<Renderer>().sharedMaterial =
                AssetLibrary.MaterialGraded(material, h);
            return go;
        }

        /// Per-object texture tiling via a property block, so objects keep sharing one
        /// material (and one draw-call batch) while showing texture at the right scale.
        static void SetTiling(GameObject go, float u, float v)
        {
            var r = go.GetComponent<Renderer>();
            // THE ASPECT CORRECTION MUST SURVIVE THIS OVERRIDE. The material
            // computed `TextureFit.Isotropic` at build time and this block
            // stomped `_MainTex_ST` with the raw pair — so the two non-square
            // textures in the pack rendered oblong on exactly the objects
            // that tile per-size, and `brick_red` (1024x512) is a facade on
            // a quarter of the buildings. The correction the material made
            // is re-made here, against the texture actually bound.
            var tex = r.sharedMaterial != null ? r.sharedMaterial.mainTexture : null;
            double tu = u, tv = v;
            if (tex != null)
                Ledger.Core.TextureFit.Isotropic(u, v, tex.width, tex.height, out tu, out tv);
            var mpb = new MaterialPropertyBlock();
            r.GetPropertyBlock(mpb);
            mpb.SetVector("_MainTex_ST", new Vector4((float)tu, (float)tv, 0, 0));
            r.SetPropertyBlock(mpb);
        }

        /// Which facade a building at `pos` wears. A hash of the ground
        /// position, so it is stable across runs (the pixel gates need that)
        /// and unrelated to build order (the stripe needed that gone).
        static int FacadePick(Vector3 pos)
        {
            int x = (int)Mathf.Round(pos.x * 4f);
            int z = (int)Mathf.Round(pos.z * 4f);
            int h = (x * 73856093) ^ (z * 19349663);
            return (h & 0x7fffffff) % 4;
        }
    }
}
