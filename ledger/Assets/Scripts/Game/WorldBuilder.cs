using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// Constructs the graybox city block from primitives. Deliberately ugly —
    /// M0 proves systems, not visuals.
    public static class WorldBuilder
    {
        public static readonly Vector3 BarDoor = new Vector3(-6, 0, 6);
        public static readonly Vector3 BarCounter = new Vector3(-8.5f, 0, 8.5f);

        static readonly List<Light> Lamps = new List<Light>();

        public static void BuildBlock()
        {
            Lamps.Clear();

            // Ground
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground";
            ground.transform.localScale = new Vector3(5, 1, 5); // 50x50m
            Tint(ground, new Color(0.32f, 0.33f, 0.34f));

            // Street cross
            MakeBox("Street_NS", new Vector3(0, 0.01f, 0), new Vector3(6, 0.02f, 50), new Color(0.22f, 0.22f, 0.23f));
            MakeBox("Street_EW", new Vector3(0, 0.01f, 0), new Vector3(50, 0.02f, 6), new Color(0.22f, 0.22f, 0.23f));

            // Buildings around the block (positions keep the street cross clear)
            var buildingSpecs = new[]
            {
                (new Vector3(-14, 0, 14), new Vector3(10, 9, 10)),
                (new Vector3(14, 0, 14), new Vector3(9, 13, 9)),
                (new Vector3(14, 0, -14), new Vector3(11, 7, 9)),
                (new Vector3(-14, 0, -14), new Vector3(9, 11, 10)),
                (new Vector3(20, 0, 0), new Vector3(6, 6, 4)),
                (new Vector3(-20, 0, 0), new Vector3(6, 8, 4)),
                (new Vector3(0, 0, 20), new Vector3(4, 5, 6)),
            };
            int i = 0;
            foreach (var (pos, size) in buildingSpecs)
            {
                float shade = 0.38f + 0.06f * (i++ % 3);
                MakeBox($"Building_{i}", pos + new Vector3(0, size.y / 2f, 0), size, new Color(shade, shade, shade + 0.02f));
            }

            BuildBar();

            // Crates for texture-of-life
            MakeBox("Crate_1", new Vector3(4.2f, 0.4f, 9), Vector3.one * 0.8f, new Color(0.45f, 0.38f, 0.28f));
            MakeBox("Crate_2", new Vector3(4.9f, 0.4f, 9.6f), Vector3.one * 0.8f, new Color(0.42f, 0.35f, 0.26f));
            MakeBox("Crate_3", new Vector3(4.5f, 1.2f, 9.3f), Vector3.one * 0.8f, new Color(0.48f, 0.4f, 0.3f));

            // Street lamps at the four corners of the crossing
            MakeLamp(new Vector3(4, 0, 4));
            MakeLamp(new Vector3(-4, 0, 4));
            MakeLamp(new Vector3(4, 0, -4));
            MakeLamp(new Vector3(-4, 0, -4));
        }

        /// The uncle's bar: an open-fronted room in the NW building's corner.
        static void BuildBar()
        {
            var floorColor = new Color(0.3f, 0.24f, 0.2f);
            var wallColor = new Color(0.42f, 0.36f, 0.3f);

            MakeBox("Bar_Floor", new Vector3(-8.5f, 0.05f, 8.5f), new Vector3(7, 0.1f, 7), floorColor);
            MakeBox("Bar_WallN", new Vector3(-8.5f, 1.75f, 12f), new Vector3(7, 3.5f, 0.3f), wallColor);
            MakeBox("Bar_WallW", new Vector3(-12f, 1.75f, 8.5f), new Vector3(0.3f, 3.5f, 7), wallColor);
            MakeBox("Bar_WallE", new Vector3(-5f, 1.75f, 10.25f), new Vector3(0.3f, 3.5f, 3.5f), wallColor);
            MakeBox("Bar_Roof", new Vector3(-8.5f, 3.6f, 8.5f), new Vector3(7.4f, 0.2f, 7.4f), new Color(0.25f, 0.22f, 0.2f));
            MakeBox("Bar_Counter", new Vector3(-8.5f, 0.55f, 7.2f), new Vector3(4.5f, 1.1f, 0.7f), new Color(0.35f, 0.25f, 0.18f));

            var barLightGo = new GameObject("Bar_Light");
            barLightGo.transform.position = new Vector3(-8.5f, 3.0f, 8.5f);
            var barLight = barLightGo.AddComponent<Light>();
            barLight.type = LightType.Point;
            barLight.range = 9;
            barLight.intensity = 1.1f;
            barLight.color = new Color(1f, 0.85f, 0.6f);
        }

        public static Light BuildSun()
        {
            var go = new GameObject("Sun");
            var sun = go.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.shadows = LightShadows.Soft;
            return sun;
        }

        static void MakeLamp(Vector3 basePos)
        {
            MakeBox($"LampPole_{Lamps.Count}", basePos + new Vector3(0, 1.75f, 0), new Vector3(0.15f, 3.5f, 0.15f), new Color(0.15f, 0.15f, 0.16f));
            var go = new GameObject($"LampLight_{Lamps.Count}");
            go.transform.position = basePos + new Vector3(0, 3.6f, 0);
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

        static GameObject MakeBox(string name, Vector3 center, Vector3 size, Color color)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = center;
            go.transform.localScale = size;
            Tint(go, color);
            return go;
        }

        static void Tint(GameObject go, Color color)
        {
            var renderer = go.GetComponent<Renderer>();
            // One material instance per object is fine at this scale.
            renderer.material.color = color;
        }
    }
}
