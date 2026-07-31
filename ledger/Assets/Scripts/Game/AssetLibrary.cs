using System.Collections.Generic;
using System.IO;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Runtime asset-ingestion pipeline. The world asks for surfaces and props by
    /// LOGICAL name ("asphalt", "brick", "streetlamp") and never touches files
    /// directly. Three tiers resolve a request, best first:
    ///
    ///   1. A purchased/authored city pack under StreamingAssets/CityPack:
    ///        textures/<name>.png|jpg          → albedo for that surface
    ///        materials/<name>.json            → per-surface tint/smoothness/metallic/tiling
    ///        props.bundle (AssetBundle)        → prop prefabs by name
    ///      Dropping a pack in requires NO code change — this is the whole point.
    ///   2. If a texture/material file is absent, a procedurally-generated texture
    ///      (tiling noise / brick / plank patterns) so the graybox already looks
    ///      like a city, not flat-shaded cubes — and CI, which ships no pack, still
    ///      gets the upgrade.
    ///   3. If even generation is not wanted, a plain tinted Standard material.
    ///
    /// Built-in render pipeline only (Standard shader). An HDRP swap is a later,
    /// deliberate step (needs in-editor RenderPipelineAsset config + HDRP/Lit
    /// shaders) and must not be attempted from a headless build.
    public static class AssetLibrary
    {
        // Logical surface names the world builds against.
        public const string Asphalt  = "asphalt";
        public const string Sidewalk = "sidewalk";
        public const string Kerb     = "kerb";
        public const string BrickRed = "brick_red";
        public const string BrickGrey= "brick_grey";
        public const string Plaster  = "plaster";
        public const string Concrete = "concrete";
        public const string Wood     = "wood";
        public const string Roof     = "roof";
        public const string Metal    = "metal";
        public const string Glass    = "glass";
        public const string Window   = "window"; // emissive-capable; lit at night via MPB

        static bool _initialized;
        static string _packRoot;
        static AssetBundle _propBundle;
        static readonly Dictionary<string, Material> _materials = new Dictionary<string, Material>();
        static readonly Dictionary<string, Texture2D> _textures = new Dictionary<string, Texture2D>();

        public static bool PackPresent { get; private set; }

        public static void Initialize()
        {
            if (_initialized) return;
            _initialized = true;
            _packRoot = Path.Combine(Application.streamingAssetsPath, "CityPack");
            // "Present" means there is actual content to ingest, not just a docs/README
            // folder — so an empty drop-in location still falls through to procedural.
            PackPresent = Directory.Exists(_packRoot) &&
                (Directory.Exists(Path.Combine(_packRoot, "textures")) ||
                 File.Exists(Path.Combine(_packRoot, "props.bundle")));
            TryLoadPropBundle();
            Debug.Log(PackPresent
                ? $"AssetLibrary: city pack found at {_packRoot}"
                : "AssetLibrary: no city pack present — using procedural materials");
        }

        // ---- materials -------------------------------------------------------

        /// A shared, cached material for a logical surface. Shared (not instanced)
        /// so identical surfaces batch. Callers that need a per-object tweak should
        /// use a MaterialPropertyBlock rather than mutating the returned material.
        public static Material Material(string logical)
        {
            if (!_initialized) Initialize();
            if (_materials.TryGetValue(logical, out var cached)) return cached;
            var mat = BuildMaterial(logical);
            _materials[logical] = mat;
            return mat;
        }

        /// A flat, cached, SHARED material for an arbitrary colour.
        ///
        /// Cached by colour on purpose. Bodies are the one thing this game
        /// makes hundreds of, and a `new Material` per limb per person is a
        /// thousand materials, a thousand draw calls and no batching at all —
        /// which is how a crowd system that computes correctly still cannot
        /// be switched on. Rounded to 5 bits a channel before keying, or the
        /// cache never hits and the whole point is lost to float noise.
        public static Material Opaque(Color c)
        {
            if (!_initialized) Initialize();
            int key = (Mathf.RoundToInt(Mathf.Clamp01(c.r) * 31) << 10)
                    | (Mathf.RoundToInt(Mathf.Clamp01(c.g) * 31) << 5)
                    | Mathf.RoundToInt(Mathf.Clamp01(c.b) * 31);
            if (_flat.TryGetValue(key, out var cached) && cached != null) return cached;
            var shader = Shader.Find("Standard");
            var mat = new Material(shader != null ? shader : DefaultShader())
            {
                name = $"mat_flat_{key:x}",
                color = new Color(((key >> 10) & 31) / 31f, ((key >> 5) & 31) / 31f,
                                  (key & 31) / 31f, 1f),
            };
            mat.SetFloat("_Glossiness", 0.16f);
            mat.SetFloat("_Metallic", 0f);
            // GPU INSTANCING. These materials exist almost entirely to be
            // worn by bodies, and a body is thirteen boxes — so a street of
            // forty people is five hundred draws of the same two meshes in
            // the same handful of colours, which is the exact case
            // instancing was built for. One flag.
            mat.enableInstancing = true;
            _flat[key] = mat;
            return mat;
        }
        static readonly Dictionary<int, Material> _flat = new Dictionary<int, Material>();

        static Material BuildMaterial(string logical)
        {
            var spec = SurfaceSpec.For(logical);
            var shader = Shader.Find("Standard");
            var mat = new Material(shader != null ? shader : DefaultShader()) { name = "mat_" + logical };

            var tex = ResolveTexture(logical, spec);
            if (tex != null)
            {
                mat.mainTexture = tex;
                // NOT EVERY SOURCE IS SQUARE, and `Tiling` was authored as
                // though every source were. Two of the twelve in the first real
                // pack came back 1024x512, and a uniform factor on those puts
                // twice as many texels across a metre as up it — oblong mortar
                // courses, a stretched kerb. `TextureFit` corrects the shape
                // and leaves square sources, which is all of the procedural
                // ones, bit-for-bit alone.
                TextureFit.Isotropic(spec.Tiling.x, spec.Tiling.y,
                                     tex.width, tex.height,
                                     out double tx, out double ty);
                mat.mainTextureScale = new Vector2((float)tx, (float)ty);
            }
            mat.color = spec.Tint;
            // Standard shader (built-in): _Glossiness is smoothness, _Metallic is 0..1.
            mat.SetFloat("_Glossiness", spec.Smoothness);
            mat.SetFloat("_Metallic", spec.Metallic);

            if (spec.Emission != Color.black)
            {
                mat.EnableKeyword("_EMISSION");
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                mat.SetColor("_EmissionColor", spec.Emission);
            }
            return mat;
        }

        /// WET GROUND (the-gap.md §3a, LightModel.Smoothness/AlbedoScale).
        ///
        /// Driven onto the SHARED material, so every road slab and pavement in
        /// the city changes together in one assignment rather than per-object.
        ///
        /// The mistake this exists to avoid is raising smoothness alone. A
        /// water film fills the surface micro-structure, so less light
        /// scatters back out AND more reflects specularly — wet asphalt is
        /// shinier and DARKER. Shiny-but-not-darker is polished plastic, and
        /// it is why so many rainy game streets look like a car showroom
        /// floor.
        public static void SetWetness(float wetness)
        {
            if (!_initialized) return;
            wetness = Mathf.Clamp01(wetness);
            if (Mathf.Abs(wetness - _wetness) < 0.002f) return;   // shared material, so this is a global write
            _wetness = wetness;
            double albedo = LightModel.AlbedoScale(wetness);
            foreach (var name in WetSurfaces)
            {
                if (!_materials.TryGetValue(name, out var mat) || mat == null) continue;
                var spec = SurfaceSpec.For(name);
                mat.SetFloat("_Glossiness", (float)LightModel.Smoothness(spec.Smoothness, wetness));
                mat.color = new Color(spec.Tint.r * (float)albedo, spec.Tint.g * (float)albedo,
                                      spec.Tint.b * (float)albedo, spec.Tint.a);
            }
        }
        static float _wetness = -1f;

        /// POSITIVE CONTROL for the reflection A/B.
        ///
        /// Switching the probe off measured a change of exactly zero on a
        /// road at 0.90 wetness, and there are two very different reasons
        /// that could happen: the probe is not reaching the shading at all,
        /// or wet specular contributes nothing worth seeing in the first
        /// place. A single toggle cannot tell those apart, and guessing
        /// between them is a build cycle each.
        ///
        /// So: force the smoothness of every wet surface to zero. That
        /// removes the specular term by a route that cannot fail to work —
        /// it is a material property the shader reads directly, with no probe
        /// mechanics in between. If THIS moves the frame and switching the
        /// probe off does not, the answer is that the probe is not the thing
        /// lighting the road.
        public static void DefeatWetSpecular(bool defeat)
        {
            if (!_initialized) return;
            foreach (var name in WetSurfaces)
            {
                if (!_materials.TryGetValue(name, out var mat) || mat == null) continue;
                var spec = SurfaceSpec.For(name);
                mat.SetFloat("_Glossiness", defeat
                    ? 0f
                    : (float)LightModel.Smoothness(spec.Smoothness, _wetness));
            }
        }

        /// Ground the rain lands on. Walls and roofs are deliberately absent —
        /// a vertical brick face does not pool water, and wetting everything
        /// uniformly is the other half of why rainy scenes read as plastic.
        static readonly string[] WetSurfaces = { Asphalt, Sidewalk, Kerb, Concrete };

        static Shader DefaultShader()
        {
            // Standard is always in the build because primitives use it, but guard anyway.
            var probe = GameObject.CreatePrimitive(PrimitiveType.Quad);
            var s = probe.GetComponent<Renderer>().sharedMaterial.shader;
            Object.Destroy(probe);
            return s;
        }

        // ---- textures --------------------------------------------------------

        static Texture2D ResolveTexture(string logical, SurfaceSpec spec)
        {
            if (_textures.TryGetValue(logical, out var cached)) return cached;

            Texture2D tex = LoadPackTexture(logical) ?? ProceduralTexture.Generate(logical, spec);
            if (tex != null)
            {
                tex.wrapMode = TextureWrapMode.Repeat;
                tex.filterMode = FilterMode.Bilinear;
            }
            _textures[logical] = tex;
            return tex;
        }

        static Texture2D LoadPackTexture(string logical)
        {
            if (!PackPresent) return null;
            foreach (var ext in new[] { ".png", ".jpg", ".jpeg" })
            {
                var path = Path.Combine(_packRoot, "textures", logical + ext);
                if (!File.Exists(path)) continue;
                try
                {
                    var bytes = File.ReadAllBytes(path);
                    var tex = new Texture2D(2, 2, TextureFormat.RGBA32, true);
                    if (tex.LoadImage(bytes))
                    {
                        // AND THE GAME CHECKS THE SHAPE ITSELF, rather than
                        // trusting that `pack_check` ran. A pack is a directory
                        // anybody can drop a file into — CI is not in that
                        // path — and a texture whose sides are not powers of
                        // two gives a mip chain that stops halving cleanly and
                        // an aspect correction that is irrational. Falling back
                        // to the procedural surface is the right answer, and
                        // saying so is the difference between a fallback and a
                        // silent one.
                        if (!TextureFit.IsCleanShape(tex.width, tex.height))
                        {
                            Debug.LogWarning(
                                $"AssetLibrary: {logical} is {tex.width}x{tex.height} — each side "
                                + "must be a power of two. Using the procedural surface instead.");
                            UnityEngine.Object.Destroy(tex);
                            return null;
                        }
                        tex.name = "packtex_" + logical;
                        return tex;
                    }
                }
                catch (System.Exception e) { Debug.LogWarning($"AssetLibrary: failed to load {path}: {e.Message}"); }
            }
            return null;
        }

        // ---- props (optional AssetBundle) -----------------------------------

        static void TryLoadPropBundle()
        {
            if (!PackPresent) return;
            var path = Path.Combine(_packRoot, "props.bundle");
            if (!File.Exists(path)) return;
            try { _propBundle = AssetBundle.LoadFromFile(path); }
            catch (System.Exception e) { Debug.LogWarning($"AssetLibrary: prop bundle load failed: {e.Message}"); }
        }

        /// Instantiate a pack prop by name if the bundle provides it; otherwise the
        /// caller falls back to primitive geometry. Returns null when unavailable.
        public static GameObject TryInstantiateProp(string name, Vector3 position, Quaternion rotation)
        {
            if (_propBundle == null) return null;
            var prefab = _propBundle.LoadAsset<GameObject>(name);
            if (prefab == null) return null;
            return Object.Instantiate(prefab, position, rotation);
        }
    }

    /// Per-surface appearance: tint, PBR params, tiling, procedural pattern kind,
    /// optional emission. Overridable by StreamingAssets/CityPack/materials/<name>.json.
    struct SurfaceSpec
    {
        public Color Tint;
        public float Smoothness;
        public float Metallic;
        public Vector2 Tiling;
        public Color Emission;
        public string Pattern; // noise | slab | brick | plank | flat

        public static SurfaceSpec For(string logical)
        {
            SurfaceSpec s;
            switch (logical)
            {
                // PALETTE SWEEP (art plan §4, "restricted palette enforced
                // across every existing material") — the one item of the
                // concrete first pass that the art commit never did. The
                // lighting was moved to stylised noir and the materials were
                // left where they had always been, which is why the world
                // read as generically grey rather than as a chosen palette.
                //
                // The rule, applied uniformly: pull everything toward
                // BLUE-GREY and DESATURATE it, so the only warm things in the
                // frame are the sodium lamps and the neon. Contrast is the
                // whole look, and contrast is a relationship — you cannot get
                // it by making the lights warmer if the walls are warm too.
                // Brick keeps the most of its own colour because a street
                // with no red left in it stops being a place and becomes a
                // mood board.
                case AssetLibrary.Asphalt:  s = Make(new Color(0.16f,0.17f,0.20f), 0.18f, 0f, new Vector2(6,6),  "noise"); break;
                case AssetLibrary.Sidewalk: s = Make(new Color(0.42f,0.44f,0.48f), 0.10f, 0f, new Vector2(8,8),  "slab");  break;
                case AssetLibrary.Kerb:     s = Make(new Color(0.46f,0.47f,0.49f), 0.12f, 0f, new Vector2(2,2),  "noise"); break;
                case AssetLibrary.BrickRed: s = Make(new Color(0.40f,0.26f,0.24f), 0.08f, 0f, new Vector2(3,4),  "brick"); break;
                case AssetLibrary.BrickGrey:s = Make(new Color(0.35f,0.36f,0.39f), 0.08f, 0f, new Vector2(3,4),  "brick"); break;
                case AssetLibrary.Plaster:  s = Make(new Color(0.50f,0.50f,0.50f), 0.06f, 0f, new Vector2(2,3),  "noise"); break;
                case AssetLibrary.Concrete: s = Make(new Color(0.37f,0.39f,0.42f), 0.10f, 0f, new Vector2(2,3),  "noise"); break;
                case AssetLibrary.Wood:     s = Make(new Color(0.28f,0.22f,0.18f), 0.20f, 0f, new Vector2(1,2),  "plank"); break;
                case AssetLibrary.Roof:     s = Make(new Color(0.17f,0.18f,0.20f), 0.12f, 0.1f, new Vector2(4,4),"noise"); break;
                case AssetLibrary.Metal:    s = Make(new Color(0.30f,0.31f,0.33f), 0.55f, 0.9f, new Vector2(1,1),"flat");  break;
                case AssetLibrary.Glass:    s = Make(new Color(0.20f,0.28f,0.32f), 0.90f, 0.2f, new Vector2(1,1),"flat");
                                            s.Emission = new Color(0.05f,0.06f,0.08f); break;
                case AssetLibrary.Window:   s = Make(new Color(0.09f,0.10f,0.13f), 0.85f, 0.1f, new Vector2(1,1),"flat");
                                            // Non-black emission so the _EMISSION keyword is
                                            // enabled on the shared material; the per-window
                                            // glow is then driven by a MaterialPropertyBlock.
                                            s.Emission = new Color(0.02f,0.02f,0.02f); break;
                default:                    s = Make(new Color(0.5f,0.5f,0.5f), 0.1f, 0f, new Vector2(2,2), "noise"); break;
            }
            return s;
        }

        static SurfaceSpec Make(Color tint, float smooth, float metal, Vector2 tiling, string pattern) =>
            new SurfaceSpec { Tint = tint, Smoothness = smooth, Metallic = metal, Tiling = tiling,
                              Emission = Color.black, Pattern = pattern };
    }

    /// Generates small tiling albedo textures so surfaces read as material, not flat
    /// paint, with zero art assets. Deterministic (Perlin + hashed jitter) so builds
    /// are reproducible. Replaced automatically when a real pack texture exists.
    static class ProceduralTexture
    {
        const int Size = 256;

        public static Texture2D Generate(string logical, SurfaceSpec spec)
        {
            var tex = new Texture2D(Size, Size, TextureFormat.RGBA32, true) { name = "proc_" + logical };
            var px = new Color32[Size * Size];
            switch (spec.Pattern)
            {
                case "brick": Brick(px, spec.Tint); break;
                case "slab":  Slab(px, spec.Tint);  break;
                case "plank": Plank(px, spec.Tint); break;
                case "flat":  Flat(px, spec.Tint);  break;
                default:      Noise(px, spec.Tint, 0.10f); break;
            }
            tex.SetPixels32(px);
            tex.Apply(true);
            return tex;
        }

        static void Noise(Color32[] px, Color baseCol, float amp)
        {
            for (int y = 0; y < Size; y++)
                for (int x = 0; x < Size; x++)
                {
                    float n = Fbm(x * 0.05f, y * 0.05f);
                    float d = (n - 0.5f) * 2f * amp;
                    px[y * Size + x] = Shade(baseCol, d);
                }
        }

        static void Brick(Color32[] px, Color baseCol)
        {
            // brick 64 wide x 32 tall, half-offset alternate rows, ~4px mortar.
            const int bw = 64, bh = 32, mortar = 4;
            var mortarCol = new Color(0.72f, 0.70f, 0.66f);
            for (int y = 0; y < Size; y++)
            {
                int row = y / bh;
                int offset = (row % 2) * (bw / 2);
                for (int x = 0; x < Size; x++)
                {
                    int bx = (x + offset) % bw;
                    int by = y % bh;
                    bool isMortar = by < mortar || bx < mortar;
                    if (isMortar) { px[y * Size + x] = Shade(mortarCol, Jitter(x, y) * 0.05f); continue; }
                    // per-brick tone variation keyed on brick cell
                    int cell = ((y / bh) * 977 + ((x + offset) / bw) * 131) & 255;
                    float tone = (cell / 255f - 0.5f) * 0.16f;
                    float n = (Fbm(x * 0.08f, y * 0.08f) - 0.5f) * 0.10f;
                    px[y * Size + x] = Shade(baseCol, tone + n);
                }
            }
        }

        static void Slab(Color32[] px, Color baseCol)
        {
            // paving slabs: light grid grooves over subtle noise.
            const int s = 64, groove = 3;
            for (int y = 0; y < Size; y++)
                for (int x = 0; x < Size; x++)
                {
                    bool g = (x % s) < groove || (y % s) < groove;
                    float n = (Fbm(x * 0.06f, y * 0.06f) - 0.5f) * 0.08f;
                    float d = g ? -0.14f : n;
                    px[y * Size + x] = Shade(baseCol, d);
                }
        }

        static void Plank(Color32[] px, Color baseCol)
        {
            // horizontal planks with grain streaks and thin seams.
            const int ph = 32, seam = 2;
            for (int y = 0; y < Size; y++)
                for (int x = 0; x < Size; x++)
                {
                    bool s = (y % ph) < seam;
                    float grain = Mathf.Sin((x * 0.3f) + Fbm(x * 0.02f, y * 0.2f) * 6f) * 0.05f;
                    int plank = y / ph;
                    float tone = ((plank * 53 & 15) / 15f - 0.5f) * 0.12f;
                    float d = s ? -0.18f : grain + tone;
                    px[y * Size + x] = Shade(baseCol, d);
                }
        }

        static void Flat(Color32[] px, Color baseCol)
        {
            var c = (Color32)baseCol;
            for (int i = 0; i < px.Length; i++) px[i] = c;
        }

        // fractal Brownian motion from Perlin octaves, 0..1
        static float Fbm(float x, float y)
        {
            float v = 0f, amp = 0.5f, freq = 1f;
            for (int o = 0; o < 4; o++)
            {
                v += amp * Mathf.PerlinNoise(x * freq, y * freq);
                freq *= 2f; amp *= 0.5f;
            }
            return Mathf.Clamp01(v);
        }

        static float Jitter(int x, int y)
        {
            int h = (x * 73856093) ^ (y * 19349663);
            return ((h & 255) / 255f) - 0.5f;
        }

        static Color32 Shade(Color baseCol, float delta)
        {
            return new Color(
                Mathf.Clamp01(baseCol.r + delta),
                Mathf.Clamp01(baseCol.g + delta),
                Mathf.Clamp01(baseCol.b + delta), 1f);
        }
    }
}
