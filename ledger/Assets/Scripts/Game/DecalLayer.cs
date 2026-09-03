using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// THE SURFACE-HISTORY LAYER (M17.10 V2) — stains, tar seams, road wear
    /// and damp on the walls. The reference set's overcast frame is the
    /// argument for this whole class: a street with no interesting light in
    /// it still reads real when every surface carries its past.
    ///
    /// TEXTURES ARE FETCHED, NOT SHIPPED IN CODE: CC0 sets from ambientCG
    /// land under StreamingAssets/Decals (the CityPack pattern — File IO +
    /// LoadImage, no editor machinery), one directory per set, Color and
    /// Opacity combined here at load. NO DIRECTORY IS NOT AN ERROR: the
    /// layer reports itself absent through `Why` and the verdict counts,
    /// and comes alive the run after the fetch lands. Rule 3b, both ways.
    ///
    /// PLACEMENT IS DETERMINISTIC — `Dressing.Roll` off position, like every
    /// other dressing decision, so the same street is dirty in the same
    /// places every run and a still can be compared against the last one.
    public static class DecalLayer
    {
        public static int RoadDecals, WallDecals;
        /// A COUNT over every road decal placed this run — not a peak, not a
        /// last-wins. Its denominator is `RoadDecals` printed beside it on the
        /// done line, and its whole job is to make ONE regression loud: see
        /// `RoadDecalY` below for the incident. Reads 0 when the layer is right.
        public static int BuriedRoadDecals;
        public static string Why = "not tried";

        /// THE BURIAL. Road decals were placed at y=0.02f — the slab's CENTRE,
        /// two centimetres UNDER the surface — for 78 consecutive runs, while
        /// `roadDecals=569` counted them present in every one of those
        /// verdicts. The shader is `ZWrite Off` with `Offset -1,-1`, which
        /// wins a coplanar tie and cannot bridge 2cm, so every one of the 569
        /// failed the depth test against the tarmac above it. A COUNT PROVES
        /// CONSTRUCTION, NOT VISIBILITY, and nothing else in the verdict was
        /// asking the second question.
        ///
        /// 0.045 is where the yellow lines already sit (WorldBuilder.cs:514):
        /// 5mm proud of the slab, and UNDER the centre dashes (0.05) and the
        /// zebra stripes (0.055) so fresh paint still reads over grime rather
        /// than the other way round.
        ///
        /// It is also exactly COPLANAR with a junction pad's top surface
        /// (WorldBuilder.cs:581 centres those at 0.025 with height 0.04),
        /// which is fine and is the case the shader was already built for:
        /// `ZWrite Off` with `ZTest LEqual` and `Offset -1,-1` wins a tie
        /// deterministically. A tie it wins; 2cm it cannot.
        ///
        /// THE PLANE IT IS COMPARED AGAINST IS NOT COPIED HERE ANY MORE.
        /// `WorldBuilder.RoadTopY` is the slab's top and this file used to
        /// carry its own `0.04f` beside a comment explaining the derivation —
        /// two implementations of one number, and the counter that exists to
        /// catch a sinking decal was reading the copy. Both would have gone
        /// stale together, which is the one way `decalsBuried` could go quiet
        /// while every decal it counts is under the tarmac.
        const float RoadDecalY = 0.045f;

        /// The multiply tint a grayscale MASK gets when it is loaded as alpha
        /// — see LoadSet. 0.35 is 2^-1.5, one and a half stops: about the
        /// darkest a wet oil stain takes asphalt down by, and a physical
        /// derivation rather than a dial. At road strength 0.8 the darkest
        /// REACHABLE multiplier becomes 1-0.8*0.65 = 0.48; measured over the
        /// actual masks, the darkest pixel each one contains moves
        /// SurfaceImperfections003 0.800 -> 0.543, 012 0.800 -> 0.479,
        /// and on walls at 0.7, 001 0.825 -> 0.619, 007 and Scratches003
        /// 0.825 -> 0.544. Those 0.80/0.825 numbers are not a coincidence,
        /// they are the arithmetic in LoadSet's comment.
        const byte MaskTint = 89;   // 0.35 * 255

        static readonly List<Material> _mats = new List<Material>();
        static readonly List<Texture2D> _roadTex = new List<Texture2D>();
        static readonly List<int> _roadWeight = new List<int>();
        static readonly List<Texture2D> _wallTex = new List<Texture2D>();
        static readonly List<int> _wallWeight = new List<int>();
        static Mesh _quad;

        /// Which fetched sets dress ROADS and which dress WALLS. Names match
        /// the ambientCG ids fetch_visual.py banks; a set that has not
        /// arrived is skipped and counted absent.
        ///
        /// `RoadLines001` IS DELIBERATELY NOT HERE. It is the one road set
        /// that shipped with no Opacity map, so LoadSet took the inverse-luma
        /// fallback below — and on a photograph of road paint the asphalt is
        /// the DARK half and the lines are the light half, so the fallback
        /// made the asphalt opaque and the lines transparent. Measured over
        /// its own pixels (`tools/decal-ink.py --set RoadLines001`): meanAlpha
        /// 0.448 against meanLuma 0.552, ink 0.187 at the road strength, and
        /// every drop of it the background. It was not drawing worn paint, it
        /// was stamping a dark rectangle on the road.
        ///
        /// An earlier version of this paragraph called that "the highest ink of
        /// any road set in the bank", in units that were the UNSCALED 0.233
        /// rather than the strength-scaled ones the weights use. Both readings
        /// are wrong about the ranking: ManholeCover011 is 0.372 scaled and
        /// 0.465 raw, above it either way. What is true is the part that
        /// mattered — it is the highest of the RoadLines family by 4x, and its
        /// ink is on the wrong half of the picture.
        ///
        /// Dropped rather than special-cased
        /// because a correct alpha for it would have to be authored, not
        /// derived, and the other five RoadLines sets ship real Opacity maps.
        static readonly string[] RoadSets =
            { "RoadLines004", "RoadLines007", "RoadLines010",
              "RoadLines011", "RoadLines018", "AsphaltDamageSet001",
              "ManholeCover011", "SurfaceImperfections003",
              "SurfaceImperfections012" };
        /// `LeakingSubstance001` was named here for weeks and has never been
        /// on disk — `fetch_visual.py:70` asks for it, the fetch has never
        /// landed it, and the loader skipped it silently while the array read
        /// as 6-of-6. Removed rather than commented-out: this array is the
        /// roster of what dresses walls, and an entry that has never existed
        /// makes every reading of its Length a small lie. The fetch gap is
        /// the fetcher's business and it is still recorded there.
        static readonly string[] WallSets =
            { "Leaking005", "Moss001",
              "SurfaceImperfections001", "SurfaceImperfections007",
              "Scratches003" };

        /// HOW OFTEN EACH ROAD SET IS PICKED, relative to the others. A
        /// uniform pick was giving 60% of every placement to paint-line sets
        /// that a MULTIPLY decal structurally cannot draw — the lines are the
        /// WHITE part of the texture, and white is the multiply identity.
        ///
        /// Measured over the shipped 2K files, as mean(alpha*(1-luma)) times
        /// the road strength 0.8 — the actual darkening the shader lays down
        /// per pixel — AFTER the mask retint in LoadSet, whole series, not a
        /// summary:
        ///
        ///   ManholeCover011 0.372   AsphaltDamageSet001 0.113
        ///   SurfaceImperfections003 0.071   SurfaceImperfections012 0.061
        ///   RoadLines004 0.045   RoadLines018 0.041   RoadLines011 0.014
        ///   RoadLines010 0.009   RoadLines007 0.006
        ///
        /// So the top two carry 30x the bottom two and were getting the same
        /// share of the street. The weights follow that ordering with ONE
        /// deliberate departure: ink-proportional would hand ManholeCover011
        /// 51% of all placements, and a manhole cover is an OBJECT, not
        /// grime — at the 1.4-3.6m sizes and random yaw this loop uses, one
        /// every other decal reads as absurd rather than as dirty. Capped at
        /// 3/22 (14%).
        ///
        /// An unlisted set gets 1, the line tier, on purpose: a newly fetched
        /// set cannot flood the street before somebody has measured its ink.
        ///
        /// THE SERIES IS RE-DERIVABLE NOW RATHER THAN QUOTED —
        /// `python3 tools/decal-ink.py` prints every number above off the
        /// shipped files in five seconds, reads this switch to show what share
        /// each weight actually buys, and reproduces the hand measurement that
        /// set them to three decimals. Before changing a weight, run it.
        static int RoadWeight(string set)
        {
            switch (set)
            {
                case "AsphaltDamageSet001": return 6;
                case "SurfaceImperfections003": return 4;
                case "SurfaceImperfections012": return 4;
                case "ManholeCover011": return 3;
                default: return 1;
            }
        }

        /// THE SAME QUESTION FOR WALLS, and it was picking uniformly. Measured
        /// the same way, `tools/decal-ink.py`, at the wall strength 0.7 — whole
        /// series, and the damp strength 0.55 scales every one of them by 0.79
        /// and reorders none, so one series answers both:
        ///
        ///   Moss001 0.197   SurfaceImperfections001 0.072   Leaking005 0.053
        ///   SurfaceImperfections007 0.013   Scratches003 0.013
        ///
        /// 15x from top to bottom, all five getting a fifth of the wall.
        ///
        /// THE RULE IS sqrt(ink / weakest ink), ROUNDED, which is a deliberate
        /// compression rather than the road pool's near-proportional ladder:
        /// these five are the same KIND of mark at different intensities, so a
        /// 15x ink spread turned into a 15x pick spread would make a street of
        /// one stain. Square root turns it into 3.9 / 2.4 / 2.0 / 1.0 / 1.0.
        ///
        /// ONE DEPARTURE, and it is measured rather than felt: Moss001 rounds
        /// to 4 and gets 3. It is the only wall set with no Opacity map, so
        /// LoadSet gives it inverse-luma alpha and it covers `cover50=0.553` of
        /// its quad against 0.004..0.020 for the other four. Equal ink from a
        /// full-coverage texture and from a sparse one do not land equally on a
        /// wall, and ink alone cannot see that — the coverage column can.
        ///
        /// So: 3/2/2/1/1, top share 33% against a road pool whose top is 27%,
        /// and nothing below 1. Mild on purpose — this reorders the mix, it
        /// does not replace it.
        static int WallWeight(string set)
        {
            switch (set)
            {
                case "Moss001": return 3;
                case "SurfaceImperfections001": return 2;
                case "Leaking005": return 2;
                default: return 1;
            }
        }

        public static void Build()
        {
            RoadDecals = 0; WallDecals = 0; BuriedRoadDecals = 0;
            // `ambientcg` IS PART OF THE PATH. fetch_visual.py banks each set
            // under Decals/ambientcg/<ID> and this loader joined Decals/<ID>
            // — two implementations of one layout, and the first run with
            // files on disk (98d8683) read `dir_present,_no_set_loaded`
            // because every per-set Directory.Exists missed by one segment.
            // Rule 5b's twin: the loader had no run in which the files
            // existed until the fetch landed, so both halves looked right.
            var root = Path.Combine(Application.streamingAssetsPath,
                                    "Decals", "ambientcg");
            if (!Directory.Exists(root))
            {
                Why = "no decal dir; fetch not landed";
                return;
            }
            var sh = Shader.Find("Hidden/LedgerDecal");
            if (sh == null) { Why = "shader missing"; return; }

            int loaded = 0;
            foreach (var set in RoadSets)
            {
                var t = LoadSet(Path.Combine(root, set));
                // Weight appended in the SAME statement as the texture, so
                // the two lists cannot drift out of alignment when a set
                // fails to load — the parallel-array fault this project has
                // already paid for twice.
                if (t != null)
                { _roadTex.Add(t); _roadWeight.Add(RoadWeight(set)); loaded++; }
            }
            foreach (var set in WallSets)
            {
                var t = LoadSet(Path.Combine(root, set));
                // Same statement, same reason as the road pool above: two lists
                // appended apart is how a parallel array drifts.
                if (t != null)
                { _wallTex.Add(t); _wallWeight.Add(WallWeight(set)); loaded++; }
            }
            if (loaded == 0) { Why = "dir present, no set loaded"; return; }
            Why = $"{loaded}_set(s)";

            EnsureQuad();
            var parent = new GameObject("Decals").transform;

            // ---- ROADS: seams, patches, wear, the odd manhole ----
            if (_roadTex.Count > 0)
                foreach (var e in StreetMap.Edges)
                {
                    var a = StreetMap.Node(e.A); var b = StreetMap.Node(e.B);
                    if (a == null || b == null) continue;
                    double dx = b.X - a.X, dz = b.Z - a.Z;
                    double len = System.Math.Sqrt(dx * dx + dz * dz);
                    if (len < 8) continue;
                    dx /= len; dz /= len;
                    // 7m -> 3.5m. The seven-metre cadence was borrowed from
                    // the cables, which hang across a street; grime lies
                    // ALONG one, and at 7m a block read as a handful of
                    // stamps rather than as a dirty road. Halved, not opened
                    // further: every placement still goes through the same
                    // prosperity gate below, so this multiplies opportunities
                    // rather than relaxing a rule. The step is the only thing
                    // that changed, so the arithmetic says close to twice the
                    // 569 this has been printing — but that is a PREDICTION,
                    // and `roadDecals` on the next landing is what says.
                    //
                    // Same standing deal as the wall loop below, and for the
                    // same reason: these are unbatched quads and the render
                    // ladder still has no decal rung, so `meanFrame` is the
                    // guard. It has sat at 28.3-30.5ms across the last
                    // twenty-five landed runs; if this moves it out of that
                    // band the cadence comes back up and the rung gets
                    // written first.
                    for (double s = 4.0; s < len - 4.0; s += 3.5)
                    {
                        double x = a.X + dx * s, z = a.Z + dz * s;
                        // Poorer streets are dirtier — the same prosperity
                        // constants the facades and cables already read.
                        double prosperity = e.Kind == "lane" ? 0.15 : 0.55;
                        double chance = 0.25 + Dressing.Density(prosperity, false) * 0.55;
                        if (Dressing.Roll(x, z, 11) >= chance) continue;
                        // Lateral drift keeps them off the centreline crown —
                        // widened from +/-30% of the width to +/-42%, because
                        // GTA's road grime lives in the WHEEL TRACKS and in
                        // the gutter, not in a band down the middle. 42% and
                        // not 50%: this drifts the decal's CENTRE and the
                        // slab ends at 50%, so 42% keeps every centre 8% of
                        // the width inside the tarmac — 40cm on a 5m lane,
                        // 80cm on a 10m spine — while the quad itself, 1.4
                        // to 3.6m across, still spills into the gutter,
                        // which is exactly where it belongs.
                        double off = (Dressing.Roll(x, z, 12) - 0.5) * (e.Width * 0.84);
                        var pos = new Vector3(
                            (float)(x - dz * off), RoadDecalY, (float)(z + dx * off));
                        int pick = Pick(_roadWeight, Dressing.Roll(x, z, 13));
                        float size = 1.4f + (float)Dressing.Roll(x, z, 14) * 2.2f;
                        float yaw = (float)Dressing.Roll(x, z, 15) * 360f;
                        Place(parent, _roadTex[pick],
                              pos, Quaternion.Euler(90f, yaw, 0), size, 0.8f);
                        RoadDecals++;
                        // Read off the position that was actually PLACED, not
                        // off the constant, so a future camber or per-street
                        // offset cannot slip under this — and against the slab
                        // top WorldBuilder itself builds from, so the test
                        // cannot go stale in step with the thing it tests.
                        if (pos.y <= WorldBuilder.RoadTopY) BuriedRoadDecals++;
                    }
                }

            // ---- WALLS: damp bases and leak streaks, where a wall exists ----
            if (_wallTex.Count > 0)
                foreach (var e in StreetMap.Edges)
                {
                    var a = StreetMap.Node(e.A); var b = StreetMap.Node(e.B);
                    if (a == null || b == null) continue;
                    double dx = b.X - a.X, dz = b.Z - a.Z;
                    double len = System.Math.Sqrt(dx * dx + dz * dz);
                    if (len < 10) continue;
                    dx /= len; dz /= len;
                    var across = new Vector3((float)-dz, 0, (float)dx);
                    float half = (float)e.Width * 0.5f + WorldBuilder.BlockSetback;
                    // 9m -> 6m, and the per-side gate 0.6 -> 0.8. SURFACE
                    // HISTORY IS THE VISUAL SPEC'S FIRST-RANKED ITEM ("the
                    // look is carried by surface history, density, depth,
                    // light, atmosphere -- in that order"), and 216 marks
                    // across a town with 376 doors and 46 terrace blocks is
                    // about one per building face: present in the counters,
                    // invisible in the frames. Roughly doubles the count.
                    //
                    // Bounded on purpose rather than opened up: the
                    // placement rules that make these read as weathering
                    // rather than as stickers -- streaks under the
                    // roofline, damp at the base, a MassAt test so nothing
                    // scribbles over a gap, prosperity thinning the good
                    // streets -- all still apply to every one of them. This
                    // multiplies opportunities, it does not relax a rule.
                    //
                    // Judged on the stills with meanFrame as the guard.
                    // These are alpha-blended quads and the render ladder
                    // has no decal rung, so if the frame moves the count
                    // comes back down and the rung gets written first.
                    for (double s = 5.0; s < len - 5.0; s += 6.0)
                    {
                        double x = a.X + dx * s, z = a.Z + dz * s;
                        double prosperity = e.Kind == "lane" ? 0.15 : 0.55;
                        double chance = 0.20 + Dressing.Density(prosperity, false) * 0.5;
                        if (Dressing.Roll(x, z, 16) >= chance) continue;
                        var mid = new Vector3((float)x, 0, (float)z);
                        foreach (int side in new[] { -1, 1 })
                        {
                            if (Dressing.Roll(x, z, 17 + side) > 0.8) continue;
                            var wall = mid + across * (half * side);
                            // A wall must actually be there — the cables
                            // learned this the hard way (scribbles over
                            // gaps); same test, same reason.
                            if (!WorldBuilder.MassAt(wall + across * (side * 0.5f),
                                                     2.0f, out _, out _)) continue;
                            int pick = Pick(_wallWeight, Dressing.Roll(x, z, 19));
                            bool streak = Dressing.Roll(x, z, 20) < 0.45;
                            // Streaks hang under the roofline; damp sits at
                            // the base. Both face the road.
                            float h = streak
                                ? 2.6f + (float)Dressing.Roll(x, z, 21) * 2.0f
                                : 0.55f;
                            float size = streak ? 1.6f : 2.2f;
                            var pos = wall - across * (side * 0.06f)
                                    + Vector3.up * h;
                            var rot = Quaternion.LookRotation(across * side);
                            // No clamp: `Pick` returns an index into the weight
                            // list, which is appended in step with `_wallTex`,
                            // and the loop above only runs when that is
                            // non-empty. The road site indexes the same way.
                            Place(parent, _wallTex[pick],
                                  pos, rot, size, streak ? 0.7f : 0.55f);
                            WallDecals++;
                        }
                    }
                }
        }

        /// Weighted pick over the sets that actually LOADED, from one
        /// `Dressing.Roll` so placement stays deterministic and a street is
        /// dirty in the same places every run.
        ///
        /// The total is summed here rather than cached: nine adds per
        /// placement is nothing, and a cached total is one more thing that
        /// can go stale when the set list changes.
        ///
        /// ONE PICK FOR BOTH POOLS, and it takes the list because the walls
        /// needed the same thing the roads already had. Copying this loop and
        /// swapping `_roadWeight` for `_wallWeight` is the exact shape CLAUDE.md
        /// rule 1's third corollary is a list of — one idea, two
        /// implementations, and the one nobody looks at is the one missing a
        /// line. Returns an index that is always inside `weight`, so no call
        /// site needs a clamp.
        static int Pick(List<int> weight, double roll)
        {
            int total = 0;
            for (int i = 0; i < weight.Count; i++) total += weight[i];
            if (total <= 0) return 0;
            int want = (int)(roll * total);
            for (int i = 0; i < weight.Count; i++)
            {
                want -= weight[i];
                if (want < 0) return i;
            }
            return weight.Count - 1;
        }

        static void Place(Transform parent, Texture2D tex, Vector3 pos,
                          Quaternion rot, float size, float strength)
        {
            var go = new GameObject("decal");
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            go.transform.rotation = rot;
            go.transform.localScale = new Vector3(size, size, 1f);
            go.AddComponent<MeshFilter>().sharedMesh = _quad;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = MatFor(tex, strength);
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }

        /// One material per (texture, strength-bucket) so renderers SHARE
        /// materials — the precondition for any batching at all.
        static Material MatFor(Texture2D tex, float strength)
        {
            foreach (var m in _mats)
                if (m.mainTexture == tex
                    && Mathf.Abs(m.GetFloat("_Strength") - strength) < 0.01f)
                    return m;
            var sh = Shader.Find("Hidden/LedgerDecal");
            var mat = new Material(sh) { mainTexture = tex };
            mat.SetFloat("_Strength", strength);
            _mats.Add(mat);
            return mat;
        }

        /// Colour + Opacity combined into one RGBA, ambientCG's convention:
        /// a set directory holds `<ID>_2K_Color.png` beside
        /// `<ID>_2K_Opacity.png`.
        ///
        /// THREE cases, and the middle one is the one that was wrong. A set
        /// with a real colour map and a real opacity map is the easy path. A
        /// set that ships ONE grayscale image under both names is a mask
        /// pretending to be a colour map and is re-tinted below. A set with
        /// no opacity map at all falls back to inverse luminance — which is
        /// right for exactly one thing and disastrous for another, so the
        /// fallback carries its own warning.
        /// PUBLIC BECAUSE THE VIGNETTE LOADS THE SAME SETS. The D1b street
        /// applies ManholeCover011, AsphaltDamageSet001, Leaking005 and
        /// Moss001 by name from its shared JSON, and every one of them needs
        /// the three cases below: the colour-plus-opacity join, the
        /// mask-shipped-twice retint, and the inverse-luma fallback that is
        /// right for Moss001 and was disastrous for RoadLines001. A second
        /// copy of this function in `StreetVignetteHost` is the exact shape
        /// of this project's worst bugs, and the copy nobody looks at is the
        /// one missing the retint.
        public static Texture2D LoadSet(string dir)
        {
            if (!Directory.Exists(dir)) return null;
            string colour = null, opacity = null, any = null;
            foreach (var f in Directory.GetFiles(dir))
            {
                var n = Path.GetFileName(f).ToLowerInvariant();
                if (!n.EndsWith(".png") && !n.EndsWith(".jpg")) continue;
                if (n.Contains("color") || n.Contains("colour")) colour = f;
                else if (n.Contains("opacity")) opacity = f;
                if (any == null) any = f;
            }
            var main = colour ?? any;
            if (main == null) return null;
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, true);
            if (!tex.LoadImage(File.ReadAllBytes(main))) return null;

            if (opacity != null)
            {
                var op = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (op.LoadImage(File.ReadAllBytes(opacity))
                    && op.width == tex.width && op.height == tex.height)
                {
                    var c = tex.GetPixels32();
                    var o = op.GetPixels32();
                    // A MASK SHIPPED TWICE IS NOT A COLOUR MAP. Five of the
                    // fourteen sets this layer names — SurfaceImperfections
                    // 001/003/007/012 and Scratches003 — bank the SAME
                    // grayscale image under both `_Color` and `_Opacity`
                    // (byte-identical, checked with md5). Loaded so, that
                    // makes rgb == a, and the shader's
                    //     mul = lerp(1, rgb, a * strength) = 1 - s*g*(1-g)
                    // has its minimum where g(1-g) peaks, at g=0.5, giving
                    // 1 - 0.8*0.25 = 0.80 on roads and 0.825 on walls. So the
                    // stain could never take a surface below 80% however
                    // black the mask was — and the CORE of every mark, where
                    // the mask is fully white and fully opaque, multiplied by
                    // white, which is the identity. The darkest part of every
                    // stain was the invisible part.
                    //
                    // Detected rather than name-listed, so it cannot go stale
                    // when a set is refetched. Measured over the shipped
                    // files, |luma(colour) - opacity.r| is exactly 0 for all
                    // five and at least 174 for every genuine colour map
                    // (Leaking005 174, RoadLines018 206, ManholeCover011
                    // 236) — a separation wide enough that the test needs no
                    // tolerance at all.
                    bool maskOnly = true;
                    for (int i = 0; i < c.Length; i++)
                    {
                        if (maskOnly
                            && (c[i].r * 30 + c[i].g * 59 + c[i].b * 11) / 100
                               != o[i].r)
                            maskOnly = false;
                        c[i].a = o[i].r;
                    }
                    // The mask becomes SHAPE over a fixed dark tint: alpha
                    // already carries where the dirt is, and the tint carries
                    // how dark it gets. Floor drops 0.80 -> 0.48 on roads.
                    if (maskOnly)
                        for (int i = 0; i < c.Length; i++)
                        {
                            c[i].r = MaskTint;
                            c[i].g = MaskTint;
                            c[i].b = MaskTint;
                        }
                    tex.SetPixels32(c);
                    tex.Apply(true);
                }
                Object.Destroy(op);
            }
            else
            {
                // NO OPACITY MAP. Alpha becomes inverse luminance: darkness
                // IS the stain, light means nothing there.
                //
                // TRUE FOR ONE SET AND ONE ONLY. `Moss001` is the sole set
                // that reaches this branch now, and it earns it — the dark
                // clumps are the moss, the light gaps are the stone under it
                // (measured meanAlpha 0.505, ink 0.197 at the wall strength
                // 0.7 — the same units as RoadWeight's series above, and the
                // most ink of any wall set). `RoadLines001` used
                // to reach it too and it is the counter-example that got it
                // dropped from RoadSets: on a photo of road paint the DARK
                // half is the asphalt, so this rule stamped the background
                // and hid the lines. Before adding a set with no Opacity
                // map, ask which half of it is the subject.
                var c = tex.GetPixels32();
                for (int i = 0; i < c.Length; i++)
                {
                    int lum = (c[i].r * 30 + c[i].g * 59 + c[i].b * 11) / 100;
                    c[i].a = (byte)(255 - lum);
                }
                tex.SetPixels32(c);
                tex.Apply(true);
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            return tex;
        }

        /// THE ONE DECAL QUAD, and public for the same reason `LoadSet` is:
        /// its winding decides which way a decal faces, and the vignette's
        /// piece list states that convention in as many words (normal -z
        /// before rotation). Two quads with two windings is two conventions,
        /// and the second one is invisible until a decal renders backwards.
        public static Mesh Quad() { EnsureQuad(); return _quad; }

        static void EnsureQuad()
        {
            if (_quad != null) return;
            _quad = new Mesh { name = "DecalQuad" };
            _quad.vertices = new[]
            {
                new Vector3(-0.5f, -0.5f, 0), new Vector3(0.5f, -0.5f, 0),
                new Vector3(-0.5f,  0.5f, 0), new Vector3(0.5f,  0.5f, 0),
            };
            _quad.uv = new[]
            {
                new Vector2(0, 0), new Vector2(1, 0),
                new Vector2(0, 1), new Vector2(1, 1),
            };
            _quad.triangles = new[] { 0, 2, 1, 1, 2, 3 };
            _quad.RecalculateBounds();
        }
    }
}
