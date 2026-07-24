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

        public static void BuildBlock()
        {
            Lamps.Clear();
            AssetLibrary.Initialize();
            ConfigureEnvironment();

            // Ground slab (tiled so it doesn't stretch across 50m).
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground";
            ground.transform.localScale = new Vector3(5, 1, 5); // 50x50m
            ground.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Concrete);
            SetTiling(ground, 24, 24);

            BuildStreetsAndWalks();
            BuildBuildings();
            BuildBar();
            BuildProps();
            BuildLamps();
        }

        /// Built-in-pipeline environment: gradient ambient + distance fog. The per-frame
        /// colours are driven by GameController.UpdateSun; these are the static defaults.
        static void ConfigureEnvironment()
        {
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogStartDistance = 22f;
            RenderSettings.fogEndDistance = 80f;
        }

        static void BuildStreetsAndWalks()
        {
            var streetNS = MakeBox("Street_NS", new Vector3(0, 0.02f, 0), new Vector3(6, 0.04f, 50), AssetLibrary.Asphalt);
            var streetEW = MakeBox("Street_EW", new Vector3(0, 0.02f, 0), new Vector3(50, 0.04f, 6), AssetLibrary.Asphalt);
            SetTiling(streetNS, 3, 25);
            SetTiling(streetEW, 25, 3);

            // Sidewalks + kerbs flank each street arm, skipping the intersection.
            float[] arms = { 14f, -14f }; // segment centre along the street axis
            const float armLen = 22f;     // spans 3..25 (and mirror)

            foreach (var sx in new[] { 1f, -1f })   // N-S street: walks at x = ±4.25
                foreach (var cz in arms)
                {
                    MakeBox($"Walk_NS_{sx}_{cz}", new Vector3(sx * 4.25f, 0.16f, cz), new Vector3(2.5f, 0.32f, armLen), AssetLibrary.Sidewalk);
                    MakeBox($"Kerb_NS_{sx}_{cz}", new Vector3(sx * 3.05f, 0.20f, cz), new Vector3(0.2f, 0.40f, armLen), AssetLibrary.Kerb);
                }
            foreach (var sz in new[] { 1f, -1f })   // E-W street: walks at z = ±4.25
                foreach (var cx in arms)
                {
                    MakeBox($"Walk_EW_{sz}_{cx}", new Vector3(cx, 0.16f, sz * 4.25f), new Vector3(armLen, 0.32f, 2.5f), AssetLibrary.Sidewalk);
                    MakeBox($"Kerb_EW_{sz}_{cx}", new Vector3(cx, 0.20f, sz * 3.05f), new Vector3(armLen, 0.40f, 0.2f), AssetLibrary.Kerb);
                }
            // Inner corner pads at the crossing.
            foreach (var sx in new[] { 1f, -1f })
                foreach (var sz in new[] { 1f, -1f })
                    MakeBox($"WalkCorner_{sx}_{sz}", new Vector3(sx * 4.25f, 0.16f, sz * 4.25f), new Vector3(2.5f, 0.32f, 2.5f), AssetLibrary.Sidewalk);
        }

        static void BuildBuildings()
        {
            var specs = new[]
            {
                (new Vector3(-14, 0, 14), new Vector3(10, 9, 10)),
                (new Vector3(14, 0, 14), new Vector3(9, 13, 9)),
                (new Vector3(14, 0, -14), new Vector3(11, 7, 9)),
                (new Vector3(-14, 0, -14), new Vector3(9, 11, 10)),
                (new Vector3(20, 0, 0), new Vector3(6, 6, 4)),
                (new Vector3(-20, 0, 0), new Vector3(6, 8, 4)),
                (new Vector3(0, 0, 20), new Vector3(4, 5, 6)),
            };
            string[] facades = { AssetLibrary.BrickRed, AssetLibrary.Plaster, AssetLibrary.BrickGrey, AssetLibrary.Concrete };
            int i = 0;
            foreach (var (pos, size) in specs)
            {
                var body = MakeBox($"Building_{i}", pos + new Vector3(0, size.y / 2f, 0), size, facades[i % facades.Length]);
                // Tile the façade at roughly one texture repeat per 3.5m so brick keeps a
                // consistent scale across differently-sized buildings.
                SetTiling(body, Mathf.Max(1, Mathf.RoundToInt(size.x / 3.5f)), Mathf.Max(1, Mathf.RoundToInt(size.y / 3.5f)));
                // Slightly-oversized roof cap for a parapet lip.
                MakeBox($"Roof_{i}", pos + new Vector3(0, size.y + 0.15f, 0), new Vector3(size.x + 0.4f, 0.3f, size.z + 0.4f), AssetLibrary.Roof);
                i++;
            }
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
        }

        static void BuildLamps()
        {
            MakeLamp(new Vector3(4, 0, 4));
            MakeLamp(new Vector3(-4, 0, 4));
            MakeLamp(new Vector3(4, 0, -4));
            MakeLamp(new Vector3(-4, 0, -4));
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
