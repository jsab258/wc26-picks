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
        public static string Why = "not tried";

        static readonly List<Material> _mats = new List<Material>();
        static readonly List<Texture2D> _roadTex = new List<Texture2D>();
        static readonly List<Texture2D> _wallTex = new List<Texture2D>();
        static Mesh _quad;

        /// Which fetched sets dress ROADS and which dress WALLS. Names match
        /// the ambientCG ids fetch_visual.py banks; a set that has not
        /// arrived is skipped and counted absent.
        static readonly string[] RoadSets =
            { "RoadLines001", "RoadLines004", "RoadLines007", "RoadLines010",
              "RoadLines011", "RoadLines018", "AsphaltDamageSet001",
              "ManholeCover011", "SurfaceImperfections003",
              "SurfaceImperfections012" };
        static readonly string[] WallSets =
            { "Leaking005", "LeakingSubstance001", "Moss001",
              "SurfaceImperfections001", "SurfaceImperfections007",
              "Scratches003" };

        public static void Build()
        {
            RoadDecals = 0; WallDecals = 0;
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
                if (t != null) { _roadTex.Add(t); loaded++; }
            }
            foreach (var set in WallSets)
            {
                var t = LoadSet(Path.Combine(root, set));
                if (t != null) { _wallTex.Add(t); loaded++; }
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
                    // Every seven metres, the same cadence as the cables and
                    // for the same reason: close enough that a block reads
                    // dressed, far enough that it never reads tiled.
                    for (double s = 4.0; s < len - 4.0; s += 7.0)
                    {
                        double x = a.X + dx * s, z = a.Z + dz * s;
                        // Poorer streets are dirtier — the same prosperity
                        // constants the facades and cables already read.
                        double prosperity = e.Kind == "lane" ? 0.15 : 0.55;
                        double chance = 0.25 + Dressing.Density(prosperity, false) * 0.55;
                        if (Dressing.Roll(x, z, 11) >= chance) continue;
                        // Lateral drift keeps them off the centreline crown.
                        double off = (Dressing.Roll(x, z, 12) - 0.5) * (e.Width * 0.6);
                        var pos = new Vector3(
                            (float)(x - dz * off), 0.02f, (float)(z + dx * off));
                        int pick = (int)(Dressing.Roll(x, z, 13) * _roadTex.Count);
                        float size = 1.4f + (float)Dressing.Roll(x, z, 14) * 2.2f;
                        float yaw = (float)Dressing.Roll(x, z, 15) * 360f;
                        Place(parent, _roadTex[Mathf.Min(pick, _roadTex.Count - 1)],
                              pos, Quaternion.Euler(90f, yaw, 0), size, 0.8f);
                        RoadDecals++;
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
                            int pick = (int)(Dressing.Roll(x, z, 19) * _wallTex.Count);
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
                            Place(parent, _wallTex[Mathf.Min(pick, _wallTex.Count - 1)],
                                  pos, rot, size, streak ? 0.7f : 0.55f);
                            WallDecals++;
                        }
                    }
                }
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
        /// `<ID>_2K_Opacity.png`; masks (JPG sets) arrive as a single
        /// grayscale image and become their own alpha.
        static Texture2D LoadSet(string dir)
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
                    for (int i = 0; i < c.Length; i++) c[i].a = o[i].r;
                    tex.SetPixels32(c);
                    tex.Apply(true);
                }
                Object.Destroy(op);
            }
            else
            {
                // Single grayscale mask: darkness IS the stain, so alpha is
                // the inverse luminance — white paper means nothing there.
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
