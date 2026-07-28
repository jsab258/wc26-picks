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
        static readonly Color WindowLit = new Color(1.0f, 0.82f, 0.45f) * 3.0f; // warm interior glow (HDR emission)
        static readonly Color WindowDark = new Color(0.02f, 0.02f, 0.02f);
        static bool _windowsLit;

        public static void BuildBlock()
        {
            Lamps.Clear();
            Windows.Clear();
            Masses.Clear();
            Masses.AddRange(BuildBlockSpecs());
            _windowsLit = false;
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
                mat.SetColor("_EmissionColor", colour * 2.2f);
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
                light.intensity = 2.1f;
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
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogStartDistance = 22f;
            RenderSettings.fogEndDistance = 80f;
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
                bool offices = districtName == "Downtown";
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
                i++;
            }
        }

        /// Horizontal window bands per floor on all four faces, sitting slightly proud of
        /// the façade. Collected so SetWindowsLit can make them glow after dusk.
        static void AddWindows(string tag, Vector3 pos, Vector3 size)
        {
            const float floorH = 3.0f, bandH = 1.3f, proud = 0.04f;
            float wx = size.x * 0.82f, wz = size.z * 0.82f;
            int floor = 0;
            for (float y = 2.0f; y < size.y - 1.0f; y += floorH, floor++)
            {
                Windows.Add(WinBox($"{tag}_win_xP_{floor}", new Vector3(pos.x + size.x / 2f + proud, y, pos.z), new Vector3(0.08f, bandH, wz)));
                Windows.Add(WinBox($"{tag}_win_xN_{floor}", new Vector3(pos.x - size.x / 2f - proud, y, pos.z), new Vector3(0.08f, bandH, wz)));
                Windows.Add(WinBox($"{tag}_win_zP_{floor}", new Vector3(pos.x, y, pos.z + size.z / 2f + proud), new Vector3(wx, bandH, 0.08f)));
                Windows.Add(WinBox($"{tag}_win_zN_{floor}", new Vector3(pos.x, y, pos.z - size.z / 2f - proud), new Vector3(wx, bandH, 0.08f)));
            }
        }

        /// Anything else that should glow after dusk — a vehicle's headlamps,
        /// for instance. Registered rather than found, so the night pass stays a
        /// single list walk instead of a scene search.
        public static void RegisterNightLight(Renderer r)
        {
            if (r != null) Windows.Add(r);
        }

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
                if (place.Kind != "corner") AddWindows($"District_{place.Id}", pos, size);
                Masses.Add((pos, size));

                // A doorstep pad marks the schedule stop itself.
                MakeBox($"District_{place.Id}_step", stop + dir * 1.2f + new Vector3(0, 0.08f, 0),
                    new Vector3(2.2f, 0.16f, 2.2f), AssetLibrary.Sidewalk);
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
