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
        public const float WindowGlowMultiplier = 3.0f;

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

        public static void BuildBlock()
        {
            Lamps.Clear();
            Windows.Clear();
            Masses.Clear();
            Masses.AddRange(BuildBlockSpecs());
            _windowsLit = false;
            WindowPanes = 0; WindowBands = 0;
            Doors = 0;
            System.Array.Clear(PremisesBuilt, 0, PremisesBuilt.Length);
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
                gMinX = System.Math.Min(gMinX, d.AvenuesX[0]);
                gMaxX = System.Math.Max(gMaxX, d.AvenuesX[d.AvenuesX.Length - 1]);
                gMinZ = System.Math.Min(gMinZ, d.AvenuesZ[0]);
                gMaxZ = System.Math.Max(gMaxZ, d.AvenuesZ[d.AvenuesZ.Length - 1]);
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
            // Signs last: they read the finished network, and a rule the city
            // obeys without telling you is indistinguishable from a bug.
            StreetFurniture.Build();
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
                light.intensity = 2.9f;
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
        public static void TickNeon(bool night, float time)
        {
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

            // 3. Pavement and kerb around every block, with chamfered corners.
            int bi = 0;
            foreach (var b in Ledger.Core.StreetMap.Blocks)
            {
                float cx = (float)b.CentreX, cz = (float)b.CentreZ;
                float hw = (float)b.Width / 2f, hd = (float)b.Depth / 2f;
                float ch = (float)Ledger.Core.StreetMap.Chamfer;
                const float walk = 2.2f, kerbH = 0.34f;

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
        static List<(Vector3 pos, Vector3 size)> BuildBlockSpecs()
        {
            var specs = new List<(Vector3, Vector3)>();
            int bi = 0;
            foreach (var b in Ledger.Core.StreetMap.Blocks)
            {
                var rng = new System.Random(9001 + bi * 131);
                float inset = 2.6f;                       // pavement + a doorstep
                float minX = (float)b.MinX + inset, maxX = (float)b.MaxX - inset;
                float minZ = (float)b.MinZ + inset, maxZ = (float)b.MaxZ - inset;
                float w = maxX - minX, d = maxZ - minZ;
                if (w < 6 || d < 6) { bi++; continue; }

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

        /// Keep clear of the bar and of every named place's doorway — a
        /// generated terrace must not close a door the game opens.
        static bool ClashesWithAuthored(Vector3 pos, Vector3 size)
        {
            float hx = size.x / 2f + 1.5f, hz = size.z / 2f + 1.5f;
            // The bar.
            if (Mathf.Abs(pos.x + 8f) < hx + 6f && Mathf.Abs(pos.z - 8f) < hz + 6f) return true;
            foreach (var place in Ledger.Core.HookMap.Places)
                if (Mathf.Abs(pos.x - (float)place.X) < hx + 3f &&
                    Mathf.Abs(pos.z - (float)place.Z) < hz + 3f) return true;
            return false;
        }

        static readonly List<(Vector3 pos, Vector3 size)> Masses = new List<(Vector3, Vector3)>();

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
                var facade = facades[i % facades.Length];
                var body = MakeBox($"Building_{i}", pos + new Vector3(0, size.y / 2f, 0), size, facade);
                // Tile the façade at roughly one texture repeat per 3.5m so brick keeps a
                // consistent scale across differently-sized buildings.
                SetTiling(body, Mathf.Max(1, Mathf.RoundToInt(size.x / 3.5f)), Mathf.Max(1, Mathf.RoundToInt(size.y / 3.5f)));
                MakeBox($"Roof_{i}", pos + new Vector3(0, size.y + 0.15f, 0), new Vector3(size.x + 0.4f, 0.3f, size.z + 0.4f), AssetLibrary.Roof);

                AddWindows($"Bldg{i}", pos, size);
                GroundFloor($"Bldg{i}", pos, size, OutwardFrom(pos));

                // Taller buildings get a stepped setback tier — breaks the flat-box
                // silhouette into something that reads as a real building profile.
                if (size.y >= 9f)
                {
                    var upper = new Vector3(size.x * 0.62f, 3.2f, size.z * 0.62f);
                    var upBase = size.y + 0.3f;
                    var upBody = MakeBox($"Building_{i}_up", pos + new Vector3(0, upBase + upper.y / 2f, 0), upper, facade);
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
                i++;
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
                    Windows.Add(WinBox($"{tag}_win_xP_{floor}_{k}",
                        new Vector3(pos.x + size.x / 2f + proud, y, pos.z + off),
                        new Vector3(0.08f, bandH, w)));
                    Windows.Add(WinBox($"{tag}_win_xN_{floor}_{k}",
                        new Vector3(pos.x - size.x / 2f - proud, y, pos.z + off),
                        new Vector3(0.08f, bandH, w)));
                }
                for (int k = 0; k < (ground ? 1 : nx); k++)
                {
                    float off = ground ? 0f : -runX / 2f + paneX / 2f + k * (paneX + gap);
                    float w = ground ? runX * 0.92f : paneX;
                    Windows.Add(WinBox($"{tag}_win_zP_{floor}_{k}",
                        new Vector3(pos.x + off, y, pos.z + size.z / 2f + proud),
                        new Vector3(w, bandH, 0.08f)));
                    Windows.Add(WinBox($"{tag}_win_zN_{floor}_{k}",
                        new Vector3(pos.x + off, y, pos.z - size.z / 2f - proud),
                        new Vector3(w, bandH, 0.08f)));
                }
            }
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

            // The fascia: a band over the shopfront, at the height the ground
            // floor ends. Proud of the wall so it reads as a ledge rather than
            // as paint. A house does not get one — a signboard over somebody's
            // front room is the fastest way to make a residential street look
            // like a high street.
            if (Ledger.Core.Dressing.HasFascia(kind))
            {
                var fasciaSize = alongX
                    ? new Vector3(0.25f, 0.55f, width * 0.9f)
                    : new Vector3(width * 0.9f, 0.55f, 0.25f);
                MakeBox($"{tag}_fascia", face + new Vector3(0, 3.5f, 0), fasciaSize,
                        AssetLibrary.Roof);
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
            if (r != null) Windows.Add(r);
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

        static Renderer WinBox(string name, Vector3 center, Vector3 size)
        {
            var go = MakeBox(name, center, size, AssetLibrary.Window);
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
            Windows.Add(WinBox("Bar_Sign", new Vector3(-6f, 2.6f, 5.1f), new Vector3(0.1f, 0.7f, 1.6f)));

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
            // Crate stack outside the bar — try a pack prop first, else primitives.
            if (AssetLibrary.TryInstantiateProp("crate_stack", new Vector3(4.5f, 0f, 9.3f), Quaternion.identity) == null)
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
        }

        static void Bench(Vector3 pos, bool alongZ = false)
        {
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
                MakeLamp(new Vector3((float)j.X + off, 0, (float)j.Z + off));
                MakeLamp(new Vector3((float)j.X - off, 0, (float)j.Z - off));
            }
            foreach (var e in Ledger.Core.StreetMap.Edges)
            {
                if (!e.Driveable || e.Length < 20) continue;
                var a = Ledger.Core.StreetMap.Node(e.A);
                var b = Ledger.Core.StreetMap.Node(e.B);
                var mid = new Vector3((float)(a.X + b.X) / 2f, 0, (float)(a.Z + b.Z) / 2f);
                bool alongZ = Mathf.Abs((float)(b.Z - a.Z)) > Mathf.Abs((float)(b.X - a.X));
                float off = (float)e.Width / 2f + 1.4f;
                MakeLamp(mid + (alongZ ? new Vector3(off, 0, 0) : new Vector3(0, 0, off)));
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
                if (!place.Planned) { i++; continue; }
                var stop = new Vector3((float)place.X, 0, (float)place.Z);
                // The mass sits BACK FROM THE STREET into its own block, so the
                // door faces the road it is addressed from. Pushing it radially
                // outward from the city centre — which is what this used to do —
                // now lands buildings in the middle of avenues.
                var block = Ledger.Core.StreetMap.BlockAt(stop.x, stop.z);
                var dir = block != null
                    ? new Vector3((float)block.CentreX - stop.x, 0, (float)block.CentreZ - stop.z).normalized
                    : new Vector3(stop.x, 0, stop.z).normalized;
                if (dir.sqrMagnitude < 0.01f) dir = Vector3.forward;
                Vector3 size = place.Kind == "home" ? new Vector3(9, 10, 8)
                    : place.Kind == "landmark" ? new Vector3(10, 7, 9)
                    : place.Kind == "business" ? new Vector3(7, 6, 7)
                    : new Vector3(4, 3, 4); // corner: a shelter, not a building
                var pos = stop + dir * (size.z / 2f + 2.5f);

                var facade = facades[i % facades.Length];
                var body = MakeBox($"District_{place.Id}", pos + new Vector3(0, size.y / 2f, 0), size, facade);
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
            MakeLamp(new Vector3(-27, 0, -5));   // outside the pawnshop
            MakeLamp(new Vector3(-25, 0, 13));   // the teahouse corner
            MakeLamp(new Vector3(29, 0, 17));    // the ferry stop
            MakeLamp(new Vector3(23, 0, -9));    // the cab rank
            MakeLamp(new Vector3(-17, 0, 19));   // the north tenements
            MakeLamp(new Vector3(-11, 0, -17));  // the bakery corner
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
                        // HOW FAR INTO THE CARRIAGEWAY THE WALL ITSELF IS, which
                        // is the only question left once the pull is bounded at
                        // the wall. Measured by walking OUT from the face plane
                        // until the road ends, so a small number means the kerb
                        // is a hand's width away and a large one means the
                        // facade stands in a lane. Nothing acts on it — it is
                        // the reading the level fix will be sized from, and a
                        // number nobody has is how the last bound came to be
                        // guessed twice.
                        var probe = at - outward * (float)Ledger.Core.Dressing.WallOffset;
                        float into = 0;
                        for (int step = 0; step < 40; step++)
                        {
                            probe += outward * 0.25f;
                            if (!Ledger.Core.StreetMap.OnRoad(probe.x, probe.z)) break;
                            into += 0.25f;
                        }
                        DressedRoadDepth.Add(into);
                    }
                }
                switch (d.Kind)
                {
                    case Ledger.Core.Clutter.Bin:
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
                        MakeBox($"Awning_{id}", at + new Vector3(0, 2.9f, 0),
                            new Vector3(2.6f, 0.1f, 1.1f), AssetLibrary.Roof);
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
            sun.shadowStrength = 0.75f;
            return sun;
        }

        static void MakeLamp(Vector3 basePos)
        {
            MakeBox($"LampPole_{Lamps.Count}", basePos + new Vector3(0, 1.75f, 0), new Vector3(0.15f, 3.5f, 0.15f), AssetLibrary.Metal);
            MakeBox($"LampHead_{Lamps.Count}", basePos + new Vector3(0, 3.55f, 0), new Vector3(0.4f, 0.2f, 0.4f), AssetLibrary.Metal);
            var go = new GameObject($"LampLight_{Lamps.Count}");
            go.transform.position = basePos + new Vector3(0, 3.5f, 0);
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 12;
            light.intensity = 1.4f;
            light.color = new Color(1f, 0.82f, 0.55f);
            light.enabled = false;
            LightShaft.Attach(light, 1.0f);
            Lamps.Add(light);
        }

        /// Counts state changes so the simulation can verify the day/night cycle ran.
        public static int LampToggleCount;
        static bool _lampsOn;

        public static void SetLampsEnabled(bool on)
        {
            if (on != _lampsOn) { _lampsOn = on; LampToggleCount++; }
            foreach (var lamp in Lamps)
                if (lamp != null && lamp.enabled != on) lamp.enabled = on;
        }

        /// Make the building windows glow (after dusk) or go dark (daytime). Emission is
        /// driven per-renderer via a property block so all windows keep sharing one
        /// material and one draw-call batch.
        public static void SetWindowsLit(bool lit)
        {
            if (lit == _windowsLit && Windows.Count > 0) return; // no-op once settled
            _windowsLit = lit;
            var color = lit ? WindowLit : WindowDark;
            var mpb = new MaterialPropertyBlock();
            foreach (var win in Windows)
            {
                if (win == null) continue;
                win.GetPropertyBlock(mpb);
                mpb.SetColor("_EmissionColor", color);
                win.SetPropertyBlock(mpb);
            }
        }

        // ---- primitive helpers ----

        static GameObject MakeBox(string name, Vector3 center, Vector3 size, string material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = center;
            go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(material);
            return go;
        }

        /// Per-object texture tiling via a property block, so objects keep sharing one
        /// material (and one draw-call batch) while showing texture at the right scale.
        static void SetTiling(GameObject go, float u, float v)
        {
            var r = go.GetComponent<Renderer>();
            var mpb = new MaterialPropertyBlock();
            r.GetPropertyBlock(mpb);
            mpb.SetVector("_MainTex_ST", new Vector4(u, v, 0, 0));
            r.SetPropertyBlock(mpb);
        }
    }
}
