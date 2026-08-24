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
        public const string Interior = "interior"; // the lit room behind shop glass

        static bool _initialized;
        static string _packRoot;
        static AssetBundle _propBundle;
        static readonly Dictionary<string, Material> _materials = new Dictionary<string, Material>();
        static readonly Dictionary<string, Texture2D> _textures = new Dictionary<string, Texture2D>();

        public static bool PackPresent { get; private set; }

        /// HOW MANY OF THE PAINT CALLS ACTUALLY LANDED.
        ///
        /// Measured off `review_street.jpg`, 24 Aug: one car in that frame
        /// sits at 0.713 median saturation when nothing else in it exceeds
        /// 0.385 — a holiday-brochure mint saloon parked on a noir street,
        /// with lilac wheels. The paint system is not missing; `TrafficHost`
        /// has a whole paragraph about repainting the kit's mint into navy,
        /// black, burgundy, bottle, grey and stone, and most of the fleet
        /// wears them.
        ///
        /// What is missing is the DENOMINATOR. Both paint sites did
        /// `mpb.SetColor("_Color", paint)` over every renderer and neither
        /// asked whether the shader HAS a `_Color` — and this project
        /// already has it written down that glTFast's shaders do not, so the
        /// property block is a silent no-op on any kit that came in that
        /// way. A paint that lands and a paint that evaporates produce the
        /// identical call, the identical log, and no complaint.
        ///
        /// So it goes through here instead, and the run reports both halves.
        /// `PaintRefusedBy` names the first shader that refused, because
        /// "three refused" and "three refused, all Unlit/glTF" are different
        /// amounts of work.
        public static int PaintTook, PaintRefused;
        public static string PaintRefusedBy = "";

        public static void ResetPaint()
        {
            PaintTook = PaintRefused = GreyRenderers = 0;
            PaintRefusedBy = "";
            // `GreyAtlases`/`GreyFailed` are NOT cleared: the greyed copies
            // are cached across a rebuild by `_greyTex`, so zeroing the count
            // would report "the swap never ran" for a town that is wearing it.
        }

        /// Paint a kit prop's renderers, counting what the shader accepted.
        /// ONE implementation, called from both sites — the repeated shape
        /// of this codebase's worst bugs is one idea with two copies, and
        /// the copy nobody looks at is the one missing a line.
        /// A LUMA-PRESERVING GREY COPY OF A KIT ATLAS, made once.
        ///
        /// MEASURED 24 Aug, which is why this exists rather than another
        /// darker palette. Multiplying `car-kit/colormap.png` by the town
        /// paints moves its top-decile saturation from 0.820 to 0.788, and
        /// `city-kit-commercial` from 0.733 to 0.686 — four to six per cent.
        /// A multiply scales all three channels and therefore PRESERVES
        /// their ratios: it darkens, and it cannot recolour. That is a
        /// virtue where `PatrolWhite`'s comment claims it (the model's own
        /// slate stripe survives) and the entire problem everywhere else,
        /// and it is why the mint saloon stayed mint through a repaint that
        /// `kitPaint=1997/0` proves landed on all 1997 renderers.
        ///
        /// So the hue goes at the SOURCE and the paint gets something
        /// neutral to colour. Luma-weighted, not an average, so the
        /// modelling survives — the shading, the panel lines and the slate
        /// stripe are all luminance, and none of them is hue.
        ///
        /// THE COLOUR SPACE IS ROUND-TRIPPED, NOT CONVERTED. `MeanTexLuma`
        /// above blits through a LINEAR target because it wants linear
        /// numbers to compare. This wants the pixels back exactly as the
        /// shader will sample them, so the RT and the destination are both
        /// sRGB — a mismatch here would shift the whole town's brightness
        /// and would not be visible until a Windows round trip.
        static Texture2D GreyCopy(Texture src)
        {
            if (src == null) return null;
            if (_greyTex.TryGetValue(src, out var cached)) return cached;
            Texture2D outTex = null;
            RenderTexture rt = null;
            var old = RenderTexture.active;
            try
            {
                int w = Mathf.Min(src.width, 1024), h = Mathf.Min(src.height, 1024);
                rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32,
                                                RenderTextureReadWrite.sRGB);
                Graphics.Blit(src, rt);
                var copy = new Texture2D(w, h, TextureFormat.RGBA32, true, false);
                RenderTexture.active = rt;
                copy.ReadPixels(new Rect(0, 0, w, h), 0, 0);
                var px = copy.GetPixels();
                for (int i = 0; i < px.Length; i++)
                {
                    float y = 0.2126f * px[i].r + 0.7152f * px[i].g + 0.0722f * px[i].b;
                    px[i] = new Color(y, y, y, px[i].a);
                }
                copy.SetPixels(px);
                copy.Apply(true);
                copy.wrapMode = TextureWrapMode.Repeat;
                outTex = copy;
                GreyAtlases++;
            }
            catch (System.Exception) { GreyFailed++; }
            finally
            {
                RenderTexture.active = old;
                if (rt != null) RenderTexture.ReleaseTemporary(rt);
            }
            _greyTex[src] = outTex;
            return outTex;
        }
        static readonly Dictionary<Texture, Texture2D> _greyTex =
            new Dictionary<Texture, Texture2D>();

        /// A VARIANT, NOT A MUTATION OF THE SHARED MATERIAL, and that is a
        /// safety decision rather than tidiness. Kit atlases are shared with
        /// props this town DELIBERATELY does not repaint — a green bench is
        /// plausible and mass-repainting on resemblance is the mistake this
        /// project has a rule about. Editing the shared material would grey
        /// them too, invisibly. One cached variant per source material keeps
        /// batching (every painted renderer gets the SAME variant) and
        /// cannot reach anything that never asked to be painted.
        static Material GreyVariant(Material src)
        {
            if (src == null) return null;
            if (_greyMat.TryGetValue(src, out var m)) return m;
            m = src;
            if (src.HasProperty("_MainTex"))
            {
                var grey = GreyCopy(src.GetTexture("_MainTex"));
                if (grey != null)
                {
                    m = new Material(src);
                    m.SetTexture("_MainTex", grey);
                    m.enableInstancing = true;
                }
            }
            _greyMat[src] = m;
            return m;
        }
        static readonly Dictionary<Material, Material> _greyMat =
            new Dictionary<Material, Material>();

        /// How many atlases were greyed, how many refused to read back, and
        /// how many renderers ended up on a greyed variant. Zero greyed with
        /// a non-zero paint count is the swap not running (rule 3b).
        public static int GreyAtlases, GreyFailed, GreyRenderers;

        public static int PaintKit(Renderer[] rends, Color c)
        {
            if (rends == null) return 0;
            int took = 0;
            var mpb = new MaterialPropertyBlock();
            foreach (var r in rends)
            {
                if (r == null) continue;
                var sm = r.sharedMaterial;
                if (sm != null && sm.HasProperty("_Color"))
                {
                    // The hue goes before the paint does, or the paint has
                    // nothing it can change (see `GreyCopy`).
                    var variant = GreyVariant(sm);
                    if (variant != null && variant != sm)
                    {
                        r.sharedMaterial = variant;
                        GreyRenderers++;
                    }
                    // READ THE EXISTING BLOCK FIRST. `SetPropertyBlock` replaces
                    // wholesale, so writing a fresh one would silently drop any
                    // property another system had already put there — the
                    // skyline path did this correctly and the two car paths did
                    // not, and folding three call sites into one helper has to
                    // keep the most careful of the three, not the commonest.
                    r.GetPropertyBlock(mpb);
                    mpb.SetColor("_Color", c);
                    r.SetPropertyBlock(mpb);
                    PaintTook++;
                    took++;
                }
                else
                {
                    PaintRefused++;
                    if (PaintRefusedBy.Length == 0)
                        PaintRefusedBy = sm != null && sm.shader != null
                            ? sm.shader.name.Replace(' ', '_') : "no_material";
                }
            }
            return took;
        }

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
        /// The same surface, in one of its variants — `brick_red` or
        /// `brick_red_b`, chosen by a hash the caller already has.
        ///
        /// THE FALLBACK IS THE POINT. A variant that never landed resolves to
        /// no texture, and a material with no texture is the flat-tint path,
        /// which would put untextured walls in a street rather than a
        /// slightly less varied one. So a variant is used only when the pack
        /// actually carries its file, and the base surface answers otherwise:
        /// the fetch can fail, partially or completely, and the city looks
        /// exactly as it does today.
        public static Material MaterialVariant(string logical, int hash)
        {
            if (!_initialized) Initialize();
            if ((hash & 1) == 0) return Material(logical);
            var alt = logical + "_b";
            if (_variantOk.TryGetValue(alt, out var ok))
                return ok ? Material(alt) : Material(logical);
            ok = PackPresent && ResolveTexture(alt, SurfaceSpec.For(alt)) != null;
            _variantOk[alt] = ok;
            if (ok) VariantsUsed++;
            return ok ? Material(alt) : Material(logical);
        }
        static readonly Dictionary<string, bool> _variantOk = new Dictionary<string, bool>();

        /// How many variant surfaces the pack actually supplied — so "the
        /// city is varied" and "the fetch landed nothing and everything fell
        /// back" cannot read the same on the done line.
        public static int VariantsUsed;

        /// THE ALBEDO-VARIETY RUNG OF V4. Every building of a given surface
        /// shared one bit-identical material, so a whole street of BrickRed
        /// was one brick — the texture variant pass doubled the choices when
        /// the pack ships `_b` files, and stopped there. Four grade steps,
        /// taken off the same position hash as the variant pick, give a
        /// terrace the look of houses painted and sooted in different
        /// decades, while staying SHARED materials (at most surfaces x
        /// variants x 3 copies exist), so batching survives.
        ///
        /// The steps average ~1.0 per channel ON PURPOSE: V1.5 just landed
        /// the noon calibration, and a variety pass that moved the street's
        /// MEAN would re-open it. Only the spread moves. The magnitudes are
        /// art values judged on stills; in linear space a step reads about
        /// half as strong as it would have pre-flip, which is why they are
        /// not 5% apart.
        static readonly Color[] FacadeGrades =
        {
            new Color(1.00f, 1.00f, 1.00f),   // as built
            new Color(0.84f, 0.84f, 0.86f),   // sooted
            new Color(1.12f, 1.10f, 1.04f),   // limewashed, slightly warm
            new Color(0.96f, 0.99f, 1.06f),   // cool, weathered
        };

        public static Material MaterialGraded(string logical, int hash)
        {
            var baseMat = MaterialVariant(logical, hash);
            GradeCalls++;
            int g = (hash >> 1) & 3;
            if (g == 0) return baseMat;
            GradedAssignments++;
            var key = baseMat.name + "#g" + g;
            if (_graded.TryGetValue(key, out var cached) && cached != null) return cached;
            var mat = new Material(baseMat) { name = key };
            // Dry colour from the same rule BuildMaterial uses, NOT from
            // baseMat.color — the base may already carry a wet darkening,
            // and copying that would bake today's weather into the paint.
            var dry = baseMat.mainTexture != null ? TextureGrade : SurfaceSpec.For(logical).Tint;
            var grade = FacadeGrades[g];
            mat.color = new Color(dry.r * grade.r, dry.g * grade.g, dry.b * grade.b, dry.a);
            _graded[key] = mat;
            // Wet-driven surfaces change colour and gloss globally in
            // SetWetness, which walks `_materials` by name and cannot see
            // this copy — so the copy registers itself, or a graded concrete
            // wall would stay dry in the rain while the pavement beside it
            // darkened. If the rain got there first, re-apply it now.
            if (System.Array.IndexOf(WetSurfaces, logical) >= 0)
            {
                _gradedWet.Add((logical, mat, grade));
                if (_wetness > 0f) { var w = _wetness; _wetness = -1f; SetWetness(w); }
            }
            return mat;
        }
        static readonly Dictionary<string, Material> _graded = new Dictionary<string, Material>();
        static readonly List<(string logical, Material mat, Color grade)> _gradedWet
            = new List<(string, Material, Color)>();

        /// Wiring proof for the grade pass (rule 6): non-neutral grades
        /// handed out / calls made. Zero on the left with a city on the
        /// right means the hash or the branch died, not that every street
        /// happened to choose the neutral coat.
        public static int GradeCalls, GradedAssignments;

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

        /// THE GRADE THAT REPLACED THE TINT-AS-COLOUR, 15 Aug — the one-line
        /// cause of the greybox.
        ///
        /// Every texture this library resolves already CARRIES its colour: a
        /// pack texture is a photograph, and a procedural one bakes
        /// `spec.Tint` into its own pixels at generation. `mat.color` then
        /// multiplied `spec.Tint` on top — squaring the palette on the
        /// procedural path and crushing the photographs on the pack path.
        /// Measured on the shipped pack: ten of twelve surfaces landed below
        /// 0.19 albedo (asphalt 0.045, windows 0.041), with film grain 2-35x
        /// louder than the texture detail that survived. Twelve real 1K
        /// photographs were invisible in every frame since 31 July, and the
        /// city read as a greybox with the textures switched ON.
        ///
        /// So: when a texture is present, the material colour is this GRADE —
        /// slightly cool, slightly desaturated, ~0.85 luminance, which keeps
        /// the noir cast without eating the albedo. The mood lives in the
        /// grade, the fog, and the post stack; the COLOUR lives in the
        /// texture, once. `spec.Tint` keeps both of its real jobs: the
        /// procedural generator's base colour, and the flat-colour fallback
        /// when no texture resolves at all.
        ///
        /// An ART value, iterated against committed stills — not a measured
        /// constant. If the street goes garish the lever is here, in one
        /// place, and the stills are the judge.
        ///
        /// ITERATION 2, from run edbce5b's numbers: at 0.82/0.84/0.88 the
        /// noon frames came back meanLuma 0.44-0.49 with 40-48% of pixels
        /// bright on three of ten days — pavements reading seaside-morning
        /// white, not overcast port. Ten percent down. Night barely moves
        /// (lamps and emission own it) and the textures stay ~4x the crushed
        /// albedo this replaced, so nothing goes back to greybox.
        static readonly Color TextureGrade = new Color(0.74f, 0.76f, 0.80f, 1f);

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
            // The grade when the texture carries the colour; the tint only
            // when nothing else does. The story is on `TextureGrade`.
            mat.color = tex != null ? TextureGrade : spec.Tint;
            // RELIEF, when the pack ships it (16 Aug, "max polish"). The
            // normal map is what makes a wall you stand next to read as
            // COURSES OF BRICK rather than as a photograph of one — and at
            // player height, standing next to walls is most of the game.
            // Same ST as the albedo, so the two cannot drift.
            // THE KEYWORD SET IS LOAD-BEARING IN THE BUILT PLAYER, and this
            // line is where three builds of dead night glow actually began.
            // Dropping the pack normal and gloss for the window surface
            // changed its keywords from the {emission, normalmap, glossmap}
            // trio — which the build has a compiled variant for, proven by
            // weeks of glowing windows — to emission alone, for which it
            // has none: Unity then silently falls back to a variant WITHOUT
            // emission, and no amount of mask/bind/revert surgery could
            // matter because the shader running had no emission term at
            // all. (It also explains the six-box probe reading flat:
            // fresh emission-only materials hit the same missing variant.)
            // So the maps stay bound even on a procedural-albedo surface:
            // the window keeps the pack's window normal and gloss — the
            // relief is a facade photograph's, invisible behind dark glass
            // at street distance — and the interior borrows the same maps
            // for the same keyword trio.
            string mapsFrom = logical == Interior ? Window : logical;
            var nrm = tex != null ? ResolveNormal(mapsFrom) : null;
            if (nrm != null)
            {
                mat.SetTexture("_BumpMap", nrm);
                mat.EnableKeyword("_NORMALMAP");
            }
            // PER-TEXEL GLOSS from the pack's roughness map (16 Aug, the
            // standing order) — worn brick sheens where the mortar does not,
            // which is most of what material realness is. EVERY SURFACE NOW,
            // ground included, which was not true until 24 Aug.
            //
            // The ground was excluded on purpose and the reason was sound:
            // SetWetness drives `_Glossiness`, and with `_METALLICGLOSSMAP`
            // bound the Standard shader ignores that scalar, so binding the
            // maps would have killed the wet-street look on the four
            // surfaces it was calibrated for — silently, without changing a
            // line of the code that writes it. The exclusion stood until
            // SetWetness could drive `_GlossMapScale` instead. It can now,
            // normalised by each map's own mean so the calibrated level is
            // untouched (reflMax 0.89 before and after); the account is on
            // `SetSmoothness`.
            //
            // THE PARAGRAPH ABOVE WAS RIGHT ABOUT THE PATH IT NAMED AND BLIND
            // TO THE TWO BESIDE IT, which is this codebase's most repeated
            // shape and worth the four lines. It reasoned carefully about
            // `SetWetness` and fixed it. Two OTHER writers of `_Glossiness`
            // on these same four surfaces were killed by the same binding and
            // nobody looked: `Weather.ApplyWetness`, which had been writing
            // into the void every frame since (deleted, 24 Aug), and
            // `DefeatWetSpecular`, the POSITIVE CONTROL whose whole claim was
            // that it worked "by a route that cannot fail" (routed through
            // `SetSmoothness`, 24 Aug). Found by grepping every
            // `SetFloat("_Glossiness"` in the Game layer, which took ten
            // seconds and should have been step two of the original change.
            //
            // (Written without quoting the ladder's own wording, because
            // slopcheck extracts C# strings and a QUOTED span inside a
            // comment reads to it as a string literal. Citing a line that
            // contains an em dash therefore lands an em dash in the prose
            // count. Same shape as this file's rule that an interpolated
            // string is code: the extractor cannot see intent, only
            // quotes.)
            //
            // asphalt_r, kerb_r and concrete_r have been on disk, fetched
            // and unused, because binding `_METALLICGLOSSMAP` makes the
            // Standard shader ignore `_Glossiness` — and `_Glossiness` is
            // the scalar `SetWetness` drives, so the wet-street look
            // calibrated on those four surfaces would have died silently.
            // `SetWetness` now drives `_GlossMapScale` instead when a map
            // is bound, normalised by the map's own mean so the CALIBRATED
            // LEVEL is unchanged and only the per-texel variation is new.
            // The account is on `SetWetness`.
            var gls = tex != null
                ? ResolveGloss(mapsFrom, (byte)Mathf.RoundToInt(spec.Metallic * 255f))
                : null;
            if (gls != null)
            {
                mat.SetTexture("_MetallicGlossMap", gls);
                mat.EnableKeyword("_METALLICGLOSSMAP");
                mat.SetFloat("_GlossMapScale", 1f);
            }
            // Standard shader (built-in): _Glossiness is smoothness, _Metallic is 0..1.
            mat.SetFloat("_Glossiness", spec.Smoothness);
            mat.SetFloat("_Metallic", spec.Metallic);

            // GPU INSTANCING, WHICH EVERY SURFACE IN THE TOWN WAS MISSING.
            //
            // `sceneRenderers=19786` against `frame[game=4.46ms
            // render+rest=20.61ms]`: the game logic is cheap and the RENDER
            // is four fifths of the frame, on geometry that is almost
            // entirely axis-aligned boxes sharing a dozen materials. That
            // is the draw-call signature, not a fill-rate one.
            //
            // The flat-colour path has had this since it was written (see
            // `Opaque`, "one flag") and every textured surface — brick,
            // plaster, concrete, road, kerb, roof, window, the whole town —
            // has not, because the flag lives on the MATERIAL and nobody
            // added it to the other constructor. One idea, two
            // implementations, and the one nobody looked at was missing
            // the line: the shape this file keeps finding.
            //
            // Safe with the property blocks already in use — per-instance
            // MPB colour is what instancing is FOR — and `MaterialVariant`
            // and `MaterialGraded` copy from this material with
            // `new Material(baseMat)`, which carries the flag, so the
            // variants and grades inherit it rather than needing a third
            // copy of this decision.
            //
            // Judged on `meanFrame` against the desktop era's own series:
            // 24.67-25.84ms across twelve runs, a tight band on one
            // machine. The cloud-era 200-1000ms readings are a different
            // regime (software rendering, no GPU) and no aggregate spans
            // the two.
            mat.enableInstancing = true;

            if (spec.Emission != Color.black)
            {
                mat.EnableKeyword("_EMISSION");
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                mat.SetColor("_EmissionColor", spec.Emission);
                // NO EMISSION MAP — DELIBERATELY, AND KEEP IT THAT WAY. Three
                // landed builds proved that binding ANY texture into this
                // player's emission slot — the panes mask via the material,
                // the panes mask via a property block, even built-in white
                // via a property block — kills the emission term outright,
                // while the unbound slot glowed for weeks. The full account
                // is on `WorldBuilder.AddWindow`. The sash structure lives
                // in the albedo; the night variation rides the per-window
                // colour scale. A future mask attempt must be an imported
                // build-time asset proven on a landed still first.
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
        /// WRITE THE SMOOTHNESS WHEREVER THIS SHADER IS ACTUALLY READING IT.
        ///
        /// Unity's Standard shader ignores `_Glossiness` the moment
        /// `_METALLICGLOSSMAP` is bound — it reads the map's alpha times
        /// `_GlossMapScale`. That is exactly why the ground surfaces were
        /// kept off the roughness maps: `SetWetness` drives the scalar, and
        /// binding a map would have made every wet-street value it writes a
        /// no-op WITHOUT changing a line of this function. A dead write
        /// that still looks like a working one.
        ///
        /// NORMALISED BY THE MAP'S OWN MEAN, so this is not a re-tuning.
        /// The calibrated target is an ABSOLUTE smoothness; a scale is a
        /// MULTIPLIER on map alpha, so writing the target straight into the
        /// scale would land the surface at target x mean — darker than
        /// every value the wet look was judged on. Dividing by the mean
        /// makes the surface AVERAGE the target and lets the map supply the
        /// variation around it, which is the whole point of having it.
        ///
        /// Clamped at 4 because a map whose mean is near zero would
        /// otherwise ask for an unbounded scale, and `_glossMean` falls
        /// back to 0.5 when a map arrived without pixels to average.
        static void SetSmoothness(Material mat, string logical, float target)
        {
            if (mat.IsKeywordEnabled("_METALLICGLOSSMAP")
                && _glossMean.TryGetValue(logical, out var mean) && mean > 0.01f)
            {
                float want = target / mean;
                // THE CLAMP WAS HIDING A MISMATCH, MEASURED 24 Aug.
                // `districtGround` fired one ray at the blown-out paving
                // strip and came back `mat_asphalt ... glossScale:4.00` —
                // pinned exactly at its ceiling. That is not a scale, it is
                // the code silently giving up: the wet target wants a
                // near-mirror and `asphalt_r` is a rough-asphalt map whose
                // mean is a quarter of it, so multiplying by 4 does not
                // raise the surface to the target, it multiplies its
                // VARIANCE by four. Hence a strip reading a p10-p90 luma
                // spread of 0.654 against 0.141 for the road beside it, and
                // a median seven times brighter under identical light.
                //
                // A WET SURFACE'S SMOOTHNESS IS THE WATER, NOT THE STONE.
                // A film of water is uniform by nature — that is what makes
                // it a mirror — so past the point where the map can no
                // longer carry the target, the map is the wrong instrument
                // and the uniform scalar is the right one. Dry keeps the
                // map, because dry is where per-texel roughness is the whole
                // point (worn brick sheening where the mortar does not).
                //
                // The threshold is not invented: it is exactly where the old
                // code began to clamp, which is where it started lying.
                if (want > 4f)
                {
                    mat.DisableKeyword("_METALLICGLOSSMAP");
                    mat.SetFloat("_Glossiness", target);
                    GlossMapDropped++;
                }
                else
                {
                    mat.SetFloat("_GlossMapScale", want);
                }
            }
            else
            {
                // Re-enable when the target comes back within the map's
                // reach, or a street that dried would stay uniform for ever
                // — a one-way switch is a ratchet (rule 5).
                if (mat.HasProperty("_MetallicGlossMap")
                    && mat.GetTexture("_MetallicGlossMap") != null
                    && _glossMean.TryGetValue(logical, out var m2) && m2 > 0.01f
                    && target / m2 <= 4f)
                {
                    mat.EnableKeyword("_METALLICGLOSSMAP");
                    mat.SetFloat("_GlossMapScale", target / m2);
                    GlossMapRestored++;
                }
                else mat.SetFloat("_Glossiness", target);
            }
        }

        /// How often the gloss map was set aside because the target had
        /// outrun it, and how often it came back. Both, because a one-way
        /// count cannot tell "the street is wet" from "the street never
        /// dried again" (rule 3b).
        public static int GlossMapDropped, GlossMapRestored;

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
                SetSmoothness(mat, name, (float)LightModel.Smoothness(spec.Smoothness, wetness));
                // Darken the GRADE, not the tint — the wet ground is textured,
                // so its base colour is `TextureGrade` (see BuildMaterial), and
                // scaling the tint here would reintroduce the crush this
                // library just stopped doing everywhere else.
                var baseCol = mat.mainTexture != null ? TextureGrade : spec.Tint;
                mat.color = new Color(baseCol.r * (float)albedo, baseCol.g * (float)albedo,
                                      baseCol.b * (float)albedo, baseCol.a);
            }
            // The graded copies of wet surfaces, same treatment with the
            // grade folded in — registered at creation, see MaterialGraded.
            foreach (var (name, mat, grade) in _gradedWet)
            {
                if (mat == null) continue;
                var spec = SurfaceSpec.For(name);
                SetSmoothness(mat, name, (float)LightModel.Smoothness(spec.Smoothness, wetness));
                var baseCol = mat.mainTexture != null ? TextureGrade : spec.Tint;
                mat.color = new Color(baseCol.r * grade.r * (float)albedo,
                                      baseCol.g * grade.g * (float)albedo,
                                      baseCol.b * grade.b * (float)albedo, baseCol.a);
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
        ///
        /// AND THE ROUTE THAT COULD NOT FAIL FAILED, SILENTLY, ON 24 AUG.
        /// This wrote `_Glossiness` directly, and binding gloss maps to
        /// every textured surface put `_METALLICGLOSSMAP` on all four wet
        /// ones — at which point the Standard shader IGNORES that scalar
        /// completely. So the positive control had been neutered, and a
        /// neutered positive control is worse than none: it reports "no
        /// change", which is read as "wet specular contributes nothing",
        /// which is the exact wrong conclusion it was built to prevent.
        ///
        /// It goes through `SetSmoothness` now, which knows about the map
        /// and drives `_GlossMapScale` when one is bound — so zero means
        /// zero again by whichever route the material actually uses. THIRD
        /// victim of that binding, found by grepping every writer of
        /// `_Glossiness` after the first two: `Weather.ApplyWetness` (dead,
        /// deleted) and this. The other three writers are on untextured
        /// materials with no map bound, so they still work.
        public static void DefeatWetSpecular(bool defeat)
        {
            if (!_initialized) return;
            foreach (var name in WetSurfaces)
            {
                if (!_materials.TryGetValue(name, out var mat) || mat == null) continue;
                var spec = SurfaceSpec.For(name);
                SetSmoothness(mat, name, defeat
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

            Texture2D tex = (spec.ProceduralOnly ? null : LoadPackTexture(logical))
                            ?? ProceduralTexture.Generate(logical, spec);
            if (tex != null)
            {
                tex.wrapMode = TextureWrapMode.Repeat;
                tex.filterMode = FilterMode.Bilinear;
            }
            _textures[logical] = tex;
            return tex;
        }

        /// The pack's normal map for a surface, SWIZZLED FOR THE SHADER.
        ///
        /// The desktop Standard shader unpacks normals as DXT5nm — x from
        /// ALPHA, y from GREEN (`UnpackScaleNormal` reads `.wy`). A JPEG
        /// normal map is plain RGB, so assigning it raw shifts every normal
        /// toward +x and the whole street lights as though raked from one
        /// side — a wrongness that reads as a lighting bug, not a texture
        /// bug, which is why it would have cost a build cycle to find on
        /// stills. Swizzled once at load: R into A, G kept, R/B slots left
        /// white (the shader reconstructs z). Linear, not sRGB, because a
        /// normal is a vector and gamma would bend every one of them.
        static Texture2D ResolveNormal(string logical)
        {
            if (_normals.TryGetValue(logical, out var cached)) return cached;
            Texture2D result = null;
            if (PackPresent)
            {
                foreach (var ext in new[] { ".png", ".jpg", ".jpeg" })
                {
                    var path = Path.Combine(_packRoot, "textures", logical + "_n" + ext);
                    if (!File.Exists(path)) continue;
                    try
                    {
                        var raw = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
                        if (raw.LoadImage(File.ReadAllBytes(path))
                            && TextureFit.IsCleanShape(raw.width, raw.height))
                        {
                            var px = raw.GetPixels32();
                            for (int i = 0; i < px.Length; i++)
                            {
                                px[i].a = px[i].r;
                                px[i].r = 255;
                                px[i].b = 255;
                            }
                            result = new Texture2D(raw.width, raw.height,
                                                   TextureFormat.RGBA32, true, true)
                            { name = "packnrm_" + logical,
                              wrapMode = TextureWrapMode.Repeat,
                              filterMode = FilterMode.Bilinear };
                            result.SetPixels32(px);
                            result.Apply(true);
                        }
                        UnityEngine.Object.Destroy(raw);
                    }
                    catch (System.Exception e)
                    { Debug.LogWarning($"AssetLibrary: normal map {path} failed: {e.Message}"); }
                    break;
                }
            }
            _normals[logical] = result;   // null cached too: ask the disk once
            return result;
        }
        static readonly Dictionary<string, Texture2D> _normals = new Dictionary<string, Texture2D>();

        /// The pack's roughness map, converted to what the built-in Standard
        /// shader actually samples: `_MetallicGlossMap`, metallic in R,
        /// SMOOTHNESS in A — so alpha is 255 minus the roughness texel, and
        /// R carries the surface's own scalar metallic (with the keyword on,
        /// the `_Metallic` scalar is ignored, so it must ride in the map).
        /// Linear, like the normal map: neither is colour data.
        static Texture2D ResolveGloss(string logical, byte metallic)
        {
            if (_gloss.TryGetValue(logical, out var cached)) return cached;
            Texture2D result = null;
            if (PackPresent)
            {
                foreach (var ext in new[] { ".png", ".jpg", ".jpeg" })
                {
                    var path = Path.Combine(_packRoot, "textures", logical + "_r" + ext);
                    if (!File.Exists(path)) continue;
                    try
                    {
                        var raw = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
                        if (raw.LoadImage(File.ReadAllBytes(path))
                            && TextureFit.IsCleanShape(raw.width, raw.height))
                        {
                            var px = raw.GetPixels32();
                            long smoothSum = 0;
                            for (int i = 0; i < px.Length; i++)
                            {
                                px[i].a = (byte)(255 - px[i].r);
                                px[i].r = metallic;
                                px[i].g = 0;
                                px[i].b = 0;
                                smoothSum += px[i].a;
                            }
                            // THE MAP'S MEAN SMOOTHNESS, banked while the
                            // pixels are already in hand. `SetWetness` needs
                            // it to keep the wet-street calibration when the
                            // ground stops using the scalar — see there.
                            _glossMean[logical] = px.Length > 0
                                ? smoothSum / (float)px.Length / 255f : 0.5f;
                            result = new Texture2D(raw.width, raw.height,
                                                   TextureFormat.RGBA32, true, true)
                            { name = "packgls_" + logical,
                              wrapMode = TextureWrapMode.Repeat,
                              filterMode = FilterMode.Bilinear };
                            result.SetPixels32(px);
                            result.Apply(true);
                        }
                        UnityEngine.Object.Destroy(raw);
                    }
                    catch (System.Exception e)
                    { Debug.LogWarning($"AssetLibrary: roughness map {path} failed: {e.Message}"); }
                    break;
                }
            }
            _gloss[logical] = result;   // null cached too: ask the disk once
            return result;
        }
        static readonly Dictionary<string, Texture2D> _gloss = new Dictionary<string, Texture2D>();
        /// Mean smoothness of each bound gloss map, 0..1.
        static readonly Dictionary<string, float> _glossMean = new Dictionary<string, float>();

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

        /// Instantiate a prop by name; the caller falls back to primitive
        /// geometry on null. TWO TIERS since 16 Aug: the pack bundle first
        /// (authored packs win), then the Resources prefabs PropPrefab
        /// builds from the fetched CC0 kit models. The name is normalised
        /// the same way PropPrefab.Key normalises — lowercase, spaces and
        /// dashes to underscores — one rule, and if the two ever disagree
        /// the miss falls through to a primitive rather than to an error.
        public static GameObject TryInstantiateProp(string name, Vector3 position, Quaternion rotation)
        {
            var key = name.ToLowerInvariant().Replace(" ", "_").Replace("-", "_");
            if (_propBundle != null)
            {
                var packed = _propBundle.LoadAsset<GameObject>(name);
                // COUNTED ON BOTH PATHS. This one returned without touching
                // the counter until 17 Aug: one idea, two implementations,
                // and the one nobody looks at is the one missing a line.
                // Latent while the bundle is null — which is exactly what
                // makes it the kind that ships.
                if (packed != null)
                {
                    PropsPlaced++;
                    var inst = Object.Instantiate(packed, position, rotation);
                    NotePropAlbedo(key, inst);
                    return inst;
                }
            }
            var prefab = Resources.Load<GameObject>("Props/Prop_" + key);
            if (prefab == null) return null;
            var go = Object.Instantiate(prefab, position, rotation);
            PropsPlaced++;
            NotePropAlbedo(key, go);
            return go;
        }

        /// How many kit-model props actually reached the world this run —
        /// the done line reads it, because "the pipeline exists" and "a
        /// mesh stood on the street" are different facts and this project
        /// has shipped that difference before (rule 6).
        public static int PropsPlaced;

        /// KIT PROPS ARRIVE WEARING WHATEVER THEIR AUTHOR PAINTED THEM, and
        /// the skyline proved what that costs: towers in holiday-brochure
        /// pastel over a noir street, brighter than everything near them.
        /// Awnings, cars and the skyline now go through repaints; benches,
        /// bins, street lights and the crate stack do not — deliberately,
        /// because a green bench is plausible and mass-repainting on
        /// resemblance alone is the rule-4 mistake. What was missing is the
        /// MEASUREMENT: which families are actually brighter than the town
        /// they stand in. Measured once per distinct key, at instantiate
        /// time — so for the repainted families (awning/car/skyline) the
        /// number is the PRE-repaint albedo; their repaints are proven by
        /// their own counters. The unrepainted four, the question being
        /// asked, carry their live value.
        ///
        /// The statistic: mean over the instance's shared materials of
        /// (linear tint luma x mean texture luma), texture read through an
        /// 8x8 GPU blit so bundle textures need no CPU readability. Equal
        /// weight per material, not per square metre — good enough to rank
        /// families against the wall reference computed by the SAME maths.
        static void NotePropAlbedo(string key, GameObject inst)
        {
            if (inst == null || _propAlbedo.ContainsKey(key)) return;
            float sum = 0f; int n = 0;
            foreach (var r in inst.GetComponentsInChildren<Renderer>(true))
                foreach (var m in r.sharedMaterials)
                {
                    if (m == null) continue;
                    sum += MatAlbedo(m); n++;
                }
            if (n > 0) _propAlbedo[key] = sum / n;
        }
        static readonly Dictionary<string, float> _propAlbedo = new Dictionary<string, float>();
        public static IEnumerable<KeyValuePair<string, float>> PropAlbedos => _propAlbedo;
        public static int PropAlbedoUnread;   // textures the blit could not read
        public static int PropAlbedoNoTex;    // materials with no texture at all

        static float MatAlbedo(UnityEngine.Material m)
        {
            var tint = m.HasProperty("_Color") ? m.color.linear : UnityEngine.Color.white;
            float tl = 0.2126f * tint.r + 0.7152f * tint.g + 0.0722f * tint.b;
            return tl * MeanTexLuma(m.mainTexture);
        }

        /// The town reference the props are compared against: the four wall
        /// surfaces' FINAL materials (grade x pack photograph), through the
        /// same helper — one instrument on both sides of the comparison, or
        /// the comparison is two instruments arguing.
        public static float TownWallAlbedo()
        {
            float sum = 0f; int n = 0;
            foreach (var logical in new[] { BrickRed, BrickGrey, Plaster, Concrete })
            {
                var m = Material(logical);
                if (m == null) continue;
                sum += MatAlbedo(m); n++;
            }
            return n > 0 ? sum / n : -1f;
        }

        static float MeanTexLuma(Texture t)
        {
            // A PROP WITH NO TEXTURE IS NOT A WHITE PROP, and until 24 Aug
            // this returned the same 1.0 for both without counting it.
            // `PropAlbedoUnread` catches the blit THROWING and cannot catch
            // this, because a null texture is not an exception — so twelve
            // `base_mesh_*` families landed in the verdict at exactly 1.00
            // against a `townWallAlbedo` of 0.15, and nothing said whether
            // that was a bin painted white or a bin with no albedo map at
            // all. Those have different fixes: one wants the skyline tint,
            // the other wants a texture. Same shape as everything else in
            // this file — a fallback that reads identically to a finding.
            if (t == null) { PropAlbedoNoTex++; return 1f; }
            if (_texLuma.TryGetValue(t, out var cached)) return cached;
            float mean = 1f;   // unreadable counts as white: a false ALARM, never a false pass
            RenderTexture rt = null;
            var old = RenderTexture.active;
            try
            {
                rt = RenderTexture.GetTemporary(8, 8, 0, RenderTextureFormat.ARGB32,
                                                RenderTextureReadWrite.Linear);
                Graphics.Blit(t, rt);
                var small = new Texture2D(8, 8, TextureFormat.RGBA32, false, true);
                RenderTexture.active = rt;
                small.ReadPixels(new Rect(0, 0, 8, 8), 0, 0);
                small.Apply(false);
                var px = small.GetPixels();
                float sum = 0f;
                for (int i = 0; i < px.Length; i++)
                    sum += 0.2126f * px[i].r + 0.7152f * px[i].g + 0.0722f * px[i].b;
                mean = sum / px.Length;
                Object.Destroy(small);
            }
            catch (System.Exception) { PropAlbedoUnread++; }
            finally
            {
                RenderTexture.active = old;
                if (rt != null) RenderTexture.ReleaseTemporary(rt);
            }
            _texLuma[t] = mean;
            return mean;
        }
        static readonly Dictionary<Texture, float> _texLuma = new Dictionary<Texture, float>();
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
        public string Pattern; // noise | slab | brick | plank | flat | panes
        /// ALBEDO never replaced by a pack photograph. The pack's
        /// `window.jpg` is a whole FACADE — brick piers around a grid of
        /// sashes — so on a window-only quad it rendered as a squeezed
        /// micro-facade. THE ALBEDO ONLY: the first version of this flag
        /// also skipped the pack normal and gloss, which changed the
        /// material's keyword set and silently killed the emission variant
        /// in the built player for three builds (the story is at the map
        /// resolution in BuildMaterial). The maps stay bound.
        public bool ProceduralOnly;

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
                case AssetLibrary.Window:   s = Make(new Color(0.09f,0.10f,0.13f), 0.85f, 0.1f, new Vector2(1,1),"panes");
                                            // Non-black emission so the _EMISSION keyword is
                                            // enabled on the shared material; the per-window
                                            // glow is then driven by a MaterialPropertyBlock.
                                            s.Emission = new Color(0.02f,0.02f,0.02f);
                                            // The pack's window.jpg is a facade, not glass —
                                            // see the field's own comment. WinBox tiles this
                                            // procedural sash per window instead.
                                            s.ProceduralOnly = true; break;
                // THE ROOM BEHIND THE SHOP GLASS (M17.10 V4). Warm and dim by
                // day; at night the occupancy sweep drives its emission like
                // any registered window, and the shelf silhouettes in front
                // turn the glow into an interior instead of a panel. Flat
                // because the walls are solid boxes — a recess would sit
                // inside the brick — and a lit backdrop behind real glass,
                // mullions and silhouettes is exactly what the PS3-era
                // reference ships. Non-black emission for the keyword, as
                // with Window; the glow itself rides the property block.
                // 0.30 -> 0.18: the first landed noon frame showed the card
                // as a bright gold panel in daylight, louder than the shop
                // around it. Darker reads as a shut interior by day and
                // changes nothing at night, where the emission carries it.
                case AssetLibrary.Interior: s = Make(new Color(0.18f,0.13f,0.08f), 0.10f, 0f, new Vector2(2,1),"noise");
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
                case "panes": Panes(px, spec.Tint); break;
                // WALLS WEATHER, ROADS DO NOT. Plaster and concrete are
                // the vertical faces that reach this branch and they get
                // the run-off; asphalt and kerb reach it too and a
                // vertical rain stain down a carriageway would be
                // nonsense. Named rather than inferred from the pattern
                // string, because "noise" is what the two groups share and
                // is exactly why one generator serves both.
                default:
                    Noise(px, spec.Tint, 0.10f,
                          logical == AssetLibrary.Plaster
                          || logical == AssetLibrary.Concrete ? 0.09f : 0f);
                    break;
            }
            tex.SetPixels32(px);
            tex.Apply(true);
            return tex;
        }

        /// `streak` is the weathering amplitude — plaster and concrete get
        /// it because they are walls that rain runs down; the ground
        /// surfaces pass 0 because a vertical run-off stain on a road is
        /// nonsense, and the same generator serves both.
        static void Noise(Color32[] px, Color baseCol, float amp, float streak = 0f)
        {
            for (int y = 0; y < Size; y++)
                for (int x = 0; x < Size; x++)
                {
                    float n = Fbm(x * 0.05f, y * 0.05f);
                    float d = (n - 0.5f) * 2f * amp;
                    if (streak > 0f) d += Streak(x, y) * streak;
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
                    // Run-off over the courses. 0.11 sits just under the
                    // per-brick tone spread (0.16) so the brick still reads
                    // as brick with weather on it rather than as a stained
                    // sheet — the streak is the second-loudest thing on the
                    // wall, not the first.
                    float w = Streak(x, y) * 0.11f;
                    px[y * Size + x] = Shade(baseCol, tone + n + w);
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

        /// Whether a texel sits on the sash: the outer frame plus one central
        /// mullion and transom, so a tile is a 2x2 of panes.
        static bool PaneFrame(int x, int y)
        {
            int edge = Mathf.Max(1, Size * 5 / 100);
            int barLo = Size / 2 - edge / 2, barHi = Size / 2 + edge / 2;
            return x < edge || x >= Size - edge
                || y < edge || y >= Size - edge
                || (x >= barLo && x <= barHi)
                || (y >= barLo && y <= barHi);
        }

        /// A window tile: glass with a dark frame, drawn by `PaneFrame`. The
        /// day half of the wall-of-light fix — the slab catcher's 1480
        /// seven-to-eleven-metre single quads — at zero geometry cost. The
        /// night half is the per-window glow SCALE in WorldBuilder: an
        /// emission-mask twin of this drawer shipped, killed the glow in
        /// the built player (any texture in that slot does — three landed
        /// builds), and was deleted rather than explained.
        static void Panes(Color32[] px, Color baseCol)
        {
            var glass = (Color32)baseCol;
            var frame = (Color32)new Color(baseCol.r * 0.25f, baseCol.g * 0.25f, baseCol.b * 0.28f);
            for (int y = 0; y < Size; y++)
                for (int x = 0; x < Size; x++)
                    px[y * Size + x] = PaneFrame(x, y) ? frame : glass;
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

        /// WEATHERING IN THE TEXTURE, WHICH IS THE ONLY PLACE IT SCALES.
        ///
        /// The visual spec ranks surface history FIRST ("surface history,
        /// density, depth, light, atmosphere -- in that order") and the
        /// decal layer is the only thing delivering any. Doubled to 368
        /// wall marks it still reads clean in the frames, because 368
        /// two-metre quads over a town of hundreds of large faces is a
        /// mark here and there, not weather. Every wall needs it, and the
        /// texture is the one layer every wall already has.
        ///
        /// VERTICAL STREAKS, and vertical is what makes them tile. A
        /// base-to-eaves gradient cannot live in a tiling albedo -- the
        /// facade repeats it 3-4 times up and bands -- but dirt washed
        /// DOWN a wall is self-similar at every height, so a streak field
        /// stretched in Y reads as decades of rain wherever the tile
        /// lands. Sampled at low frequency across and high along, which is
        /// the shape of a run-off stain.
        ///
        /// Signed and centred on zero so it darkens and lightens rather
        /// than dimming the surface: the albedo work of 15 Aug is what
        /// pulled this city out of greybox and a weathering pass that
        /// quietly subtracted 10% of it would be that regression by
        /// another route.
        static float Streak(float x, float y)
        {
            float s = Fbm(x * 0.35f, y * 0.045f);
            return (s - 0.5f) * 2f;
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
