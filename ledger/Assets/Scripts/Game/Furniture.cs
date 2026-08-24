using System.Collections.Generic;
using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// STREET FURNITURE FROM THE FETCHED KITS (M17.10 V3) — bins, bollards,
    /// benches, dock clutter, and the double-yellow lines that say BRITAIN
    /// in one glance. The reference frames are never bare: what palms and
    /// hydrants do for Los Santos, this vocabulary does for Meridian.
    ///
    /// MESHES COME THROUGH THE PROP PIPELINE: glTFast (in the manifest as of
    /// tonight) imports the Base Mesh GLBs as Models, `PropPrefab` writes
    /// them to Resources with no code change, and this class loads them by
    /// key. EVERY LOAD FAILS SOFT with a counted reason — the pipeline has a
    /// first run ahead of it, and "the package did not resolve" must read
    /// differently from "placement never ran" (rule 3b).
    ///
    /// Placement is deterministic off `Dressing.Roll`, so the same corner
    /// has the same bin every run and the stills stay comparable.
    public static class Furniture
    {
        public static int Placed, YellowLines;
        public static string Why = "not tried";
        public static readonly Dictionary<string, int> ByKind =
            new Dictionary<string, int>();

        /// Where the park benches stand — read by `NpcWalker.BenchSeatNear`,
        /// which turns a stop beside one into the `sit` activity. A bench
        /// nobody can sit on is set dressing; this list is what makes it
        /// furniture.
        public static readonly List<Vector3> BenchSeats = new List<Vector3>();

        static readonly Dictionary<string, GameObject> _prefabs =
            new Dictionary<string, GameObject>();
        static Material _yellow;

        static GameObject Prefab(string stem)
        {
            if (_prefabs.TryGetValue(stem, out var p)) return p;
            var pf = Resources.Load<GameObject>("Props/Prop_base_mesh_" + stem);
            _prefabs[stem] = pf;
            return pf;
        }

        public static void Build()
        {
            Placed = 0; YellowLines = 0; RoadNudged = 0; RoadStuck = 0;
            ByKind.Clear(); BenchSeats.Clear();
            // The probe: if the flagship mesh is missing, every other lookup
            // will be too — one legible reason instead of thirty misses.
            if (Prefab("outdoor_bin") == null)
            {
                Why = "no base-mesh prefabs; gltfast or fetch not landed";
                BuildYellowLines();     // paint needs no meshes
                return;
            }
            Why = "ok";
            var parent = new GameObject("Furniture").transform;

            foreach (var n in StreetMap.Nodes)
            {
                if (!n.IsJunction) continue;
                // A bin near most corners — the single most load-bearing
                // piece of British street furniture there is.
                if (Dressing.Roll(n.X, n.Z, 31) < 0.55)
                    PlaceAt(parent, Dressing.Roll(n.X, n.Z, 32) < 0.5
                                ? "outdoor_bin" : "swing_bin",
                            CornerSpot(n, 33), RandomYaw(n, 34));
                // The odd fingerpost where three or more ways meet.
                if (Dressing.Roll(n.X, n.Z, 35) < 0.18)
                    PlaceAt(parent, "finger_post_sign_01",
                            CornerSpot(n, 36), RandomYaw(n, 37));
            }

            foreach (var e in StreetMap.Edges)
            {
                var a = StreetMap.Node(e.A); var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 14) continue;
                dx /= len; dz /= len;
                var across = new Vector3((float)-dz, 0, (float)dx);
                // The pavement band sits between the kerb and the building
                // line; 1.1m out from the kerb keeps clear of both walkers'
                // desire lines and the wall.
                float pave = (float)e.Width * 0.5f + 1.1f;

                if (e.Kind == "lane")
                {
                    // BOLLARDS guard the lane mouths, and the lanes carry the
                    // dock clutter — pallets, barrels, the odd skip — denser
                    // where the warehouses are.
                    double share = Dressing.WarehouseShare(
                        StreetMap.DistrictAt(a.X, a.Z) ?? "");
                    for (double s = 7.0; s < len - 7.0; s += 11.0)
                    {
                        double x = a.X + dx * s, z = a.Z + dz * s;
                        double r = Dressing.Roll(x, z, 38);
                        if (r < 0.10 + share * 0.35)
                        {
                            string kind = r < 0.05 ? "skip"
                                : r < 0.10 + share * 0.18 ? "pallet"
                                : "oil_barrel";
                            int side = Dressing.Roll(x, z, 39) < 0.5 ? -1 : 1;
                            var pos = new Vector3((float)x, 0, (float)z)
                                    + across * (((float)e.Width * 0.5f - 0.8f) * side);
                            PlaceAt(parent, kind, pos, RandomYawAt(x, z, 40));
                        }
                    }
                }
                else
                {
                    // Streets and avenues: benches at long intervals, a
                    // bollard pair where a lane would tempt a car through,
                    // and DOUBLE YELLOWS along both kerbs (below).
                    for (double s = 16.0; s < len - 16.0; s += 34.0)
                    {
                        double x = a.X + dx * s, z = a.Z + dz * s;
                        if (Dressing.Roll(x, z, 41) < 0.35)
                        {
                            int side = Dressing.Roll(x, z, 42) < 0.5 ? -1 : 1;
                            var pos = new Vector3((float)x, 0, (float)z)
                                    + across * (pave * side);
                            // Benches face the road.
                            var yaw = Quaternion.LookRotation(-across * side);
                            PlaceAt(parent, "park_bench", pos, yaw);
                            BenchSeats.Add(pos);
                        }
                    }
                }
            }

            BuildYellowLines();
        }

        /// DOUBLE YELLOW LINES along the kerbs of every driveable street —
        /// pure paint, two thin strips per kerb, and the single cheapest
        /// "this is Britain" mark the whole pass owns. Unlit-ish yellow via
        /// a Standard material with full smoothness off; receives shadows so
        /// the paint darkens inside them like real paint.
        static void BuildYellowLines()
        {
            var parent = new GameObject("YellowLines").transform;
            if (_yellow == null)
            {
                var sh = Shader.Find("Standard");
                if (sh == null) return;
                _yellow = new Material(sh);
                // Worn municipal yellow, not hazard yellow.
                _yellow.color = new Color(0.78f, 0.66f, 0.18f);
                _yellow.SetFloat("_Glossiness", 0.05f);
                // 284 strips, one material, one flag — the same omission
                // AssetLibrary's textured path had. Standard supports
                // instancing; the custom shaders (blob, decal, ring,
                // worldtext) would each need a multi_compile pragma in the
                // shader before the flag bought them anything, so they are
                // deliberately left for a change that can prove itself.
                _yellow.enableInstancing = true;
            }
            foreach (var e in StreetMap.Edges)
            {
                if (!e.Driveable) continue;
                var a = StreetMap.Node(e.A); var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 10) continue;
                dx /= len; dz /= len;
                // Not every street has them — a third do, decided per edge,
                // which is how real councils paint.
                if (Dressing.Roll(a.X + dx, a.Z + dz, 43) > 0.38) continue;
                var across = new Vector3((float)-dz, 0, (float)dx);
                var mid = new Vector3(
                    (float)((a.X + b.X) * 0.5), 0.015f, (float)((a.Z + b.Z) * 0.5));
                float run = (float)len - 7.0f;
                foreach (int side in new[] { -1, 1 })
                    for (int line = 0; line < 2; line++)
                    {
                        float off = ((float)e.Width * 0.5f - 0.35f - line * 0.16f) * side;
                        var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        go.name = "yellow";
                        Object.Destroy(go.GetComponent<Collider>());
                        go.transform.SetParent(parent, false);
                        go.transform.position = mid + across * off;
                        go.transform.rotation = Quaternion.LookRotation(
                            new Vector3((float)dx, 0, (float)dz));
                        go.transform.localScale = new Vector3(0.09f, 0.012f, run);
                        var mr = go.GetComponent<MeshRenderer>();
                        mr.sharedMaterial = _yellow;
                        mr.shadowCastingMode =
                            UnityEngine.Rendering.ShadowCastingMode.Off;
                        YellowLines++;
                    }
            }
        }

        /// How many corner spots the road check had to move, and how many it
        /// could not save (all eight angles on tarmac — placed anyway,
        /// counted, so the still's bin-in-the-road has a number).
        public static int RoadNudged, RoadStuck;

        static Vector3 CornerSpot(StreetNode n, int salt)
        {
            double ang = Dressing.Roll(n.X, n.Z, salt) * System.Math.PI * 2;
            // Off the junction centre onto the pavement ring — WITH A ROAD
            // CHECK, which the first version skipped: the 3a4ea5e noon still
            // has a swing bin standing in the carriageway beside a parked
            // car, because a ring point at a junction lands on tarmac about
            // as often as not. Walk the ring in eighths until off-road.
            // Three rings, not one: the first landing read RoadStuck=25 —
            // where two avenues meet, the junction apron swallows the whole
            // r=5.5 ring and every angle is tarmac. Widen before giving up.
            var first = new Vector3((float)(n.X + System.Math.Cos(ang) * 5.5), 0,
                                    (float)(n.Z + System.Math.Sin(ang) * 5.5));
            if (!StreetMap.OnRoad(first.x, first.z)) return first;
            foreach (float r in new[] { 5.5f, 7.5f, 9.5f })
                for (int step = 1; step < 8; step++)
                {
                    double a2 = ang + step * System.Math.PI / 4;
                    var cand = new Vector3((float)(n.X + System.Math.Cos(a2) * r), 0,
                                           (float)(n.Z + System.Math.Sin(a2) * r));
                    if (!StreetMap.OnRoad(cand.x, cand.z)) { RoadNudged++; return cand; }
                }
            RoadStuck++;
            return first;
        }

        static Quaternion RandomYaw(StreetNode n, int salt) =>
            Quaternion.Euler(0, (float)Dressing.Roll(n.X, n.Z, salt) * 360f, 0);

        static Quaternion RandomYawAt(double x, double z, int salt) =>
            Quaternion.Euler(0, (float)Dressing.Roll(x, z, salt) * 360f, 0);

        static void PlaceAt(Transform parent, string stem, Vector3 pos, Quaternion rot)
        {
            // THROUGH THE PROP PIPELINE, NOT A PRIVATE Resources.Load — the
            // private path made every placement here invisible to kitAlbedo
            // (the families read 1.00 and the listing could not say which
            // placer), and it skipped the repaint: the 3a4ea5e noon still
            // has a factory-white swing bin from this file surviving the
            // build in which WorldBuilder's bins went metal. Same models,
            // same key scheme, one instrumented door.
            var propKey = "base_mesh_" + stem;
            var go = AssetLibrary.TryInstantiateProp(propKey, pos, rot);
            if (go == null) return;
            go.transform.SetParent(parent, true);
            go.name = "F_" + stem;
            // The fallback surfaces' own tints, from the same constants
            // WorldBuilder's placer uses. The fingerpost keeps municipal
            // paint — a British fingerpost IS painted white, just not
            // albedo-1.0 white.
            WorldBuilder.TintFurniture(go,
                stem == "park_bench" || stem == "pallet" ? WorldBuilder.FurnitureWood
                : stem == "finger_post_sign_01" ? FurniturePaint
                : WorldBuilder.FurnitureMetal, propKey);
            Placed++;
            ByKind[stem] = ByKind.TryGetValue(stem, out var c) ? c + 1 : 1;
        }

        /// Worn municipal paint for the fingerpost: off-white at roughly
        /// half the blown 1.00 the untextured mesh shipped with, below the
        /// brightPct instrument's 0.60 "bright pixel" line.
        static readonly Color FurniturePaint = new Color(0.55f, 0.54f, 0.50f);
    }
}
