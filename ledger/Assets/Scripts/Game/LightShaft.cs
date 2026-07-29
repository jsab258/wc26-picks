using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The cone of lit air under a lamp (the-gap.md §3a).
    ///
    /// Attached to a Light. Builds one open cone mesh, shares it across every
    /// shaft in the city, and drives its brightness from the same fog density
    /// the scene is using — so shafts appear as the air thickens with rain and
    /// night, and vanish on a clear afternoon instead of hanging there like
    /// plastic.
    ///
    /// Fails closed: no shader, no shaft, and the game is exactly as it was.
    public class LightShaft : MonoBehaviour
    {
        static Mesh _cone;
        static Shader _shader;
        static bool _probed;

        static readonly List<LightShaft> _all = new List<LightShaft>();

        Light _light;
        Material _mat;
        Renderer _renderer;
        float _baseIntensity;

        /// How far a shaft is drawn at all. Beyond this the cone is smaller
        /// than the fade would make visible and it is pure cost.
        public const float DrawDistance = 95f;

        /// From the graphics preset. Zero at Low, which switches the whole
        /// effect off — it is the most expensive thing in the scene and the
        /// first thing a preset should be allowed to take.
        public static float PresetDistance =>
            (float)Ledger.Core.Detail.ShaftDistance(
                Ledger.Core.Detail.Parse(GameSettings.Current.Detail));

        public static void Attach(Light light, float intensity = 1f)
        {
            if (light == null) return;
            if (!_probed)
            {
                _probed = true;
                _shader = Shader.Find("Hidden/LedgerLightShaft");
                if (_shader != null && !_shader.isSupported) _shader = null;
            }
            if (_shader == null) return;      // fail closed, silently
            var shaft = light.gameObject.AddComponent<LightShaft>();
            shaft._light = light;
            shaft._baseIntensity = intensity;
            shaft.Build();
        }

        void Build()
        {
            if (_cone == null) _cone = BuildCone(16);

            var go = new GameObject("Shaft");
            go.transform.SetParent(transform, false);
            // Cones point DOWN from the bulb: this is a street lamp, not a
            // searchlight.
            go.transform.localRotation = Quaternion.identity;

            var mf = go.AddComponent<MeshFilter>();
            mf.sharedMesh = _cone;
            _renderer = go.AddComponent<MeshRenderer>();
            _mat = new Material(_shader) { hideFlags = HideFlags.HideAndDontSave };
            _renderer.sharedMaterial = _mat;
            _renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _renderer.receiveShadows = false;
            // No light probes or reflection on an additive volume — it is not
            // a surface and sampling for it is wasted.
            _renderer.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
            _renderer.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;

            // Scaled to the lamp's own reach, so a short bollard and a tall
            // street lamp do not throw the same cone.
            float r = Mathf.Max(1f, _light != null ? _light.range * 0.55f : 6f);
            go.transform.localScale = new Vector3(r * 0.75f, r, r * 0.75f);

            _all.Add(this);
        }

        void OnDestroy()
        {
            _all.Remove(this);
            if (_mat != null) Destroy(_mat);
        }

        /// A/B switch for the sim's light-attribution probe. Three hundred
        /// and sixty volumetric cones are additive geometry, and the question
        /// "is the night frame bright because of the shafts?" cannot be
        /// answered by looking at a screenshot of a scene that has them.
        ///
        /// THE SETTER APPLIES IMMEDIATELY, and the first version did not.
        /// It was a plain field read by `LateUpdate`, so turning the shafts
        /// back on took effect on the NEXT frame — and the probe runs, then
        /// the night screenshot is taken, in the same one. The saved night
        /// frame was rendered with three hundred and sixty light cones
        /// missing, `nightNotDarker` went green for the wrong reason, and the
        /// grain and occlusion A/Bs that share the hour started measuring a
        /// darker street than the game has.
        ///
        /// An instrument that changes the thing it measures is worse than no
        /// instrument, because it also looks like good news.
        public static bool Enabled
        {
            get => _enabled;
            set
            {
                if (_enabled == value) return;
                _enabled = value;
                foreach (var s in _all)
                    if (s != null && s._renderer != null)
                        s._renderer.enabled = value && s._light != null
                                               && s._light.enabled && s._light.isActiveAndEnabled;
            }
        }
        static bool _enabled = true;

        /// Push the current graphics preset onto every shaft now.
        ///
        /// Without this the preset only takes effect on the next LateUpdate,
        /// which means the options slider appears to do nothing for a frame
        /// and — worse — the sim's own A/B would switch the preset, render,
        /// and measure no change, then report that the setting is
        /// decorative. That mistake has been made three times tonight with
        /// three different toggles, so this one is applied on the spot.
        public static void ApplyPreset()
        {
            bool want = _enabled && PresetDistance > 0;
            foreach (var s in _all)
            {
                if (s == null || s._renderer == null || s._light == null) continue;
                s._renderer.enabled = want && s._light.enabled && s._light.isActiveAndEnabled;
            }
        }

        void LateUpdate()
        {
            if (_mat == null || _light == null) return;

            // A shaft only exists if its lamp is on. This also means the whole
            // effect switches with the day/night cycle for free.
            bool on = _enabled && PresetDistance > 0
                      && _light.enabled && _light.isActiveAndEnabled;
            if (_renderer.enabled != on) _renderer.enabled = on;
            if (!on) return;

            // THE THING THAT MAKES IT HONEST: brightness comes from the fog
            // the scene is actually using. Clear afternoon, no shafts. Rain at
            // night, the street fills with them. A constant-intensity shaft is
            // the giveaway that it is a decal rather than lit air.
            float night = GameController.NightAmount;
            float rain = Weather.Rain;
            double density = LightModel.FogDensity(night, rain);
            // Normalised against the clear-day floor, so "some fog always"
            // does not mean "some shaft always".
            double clear = LightModel.FogDensity(0, 0);
            float scale = (float)Feel.Clamp01((density - clear) / (clear * 2.6));

            _mat.SetColor("_Color", _light.color);
            _mat.SetFloat("_Intensity", _baseIntensity * scale * 0.85f);
            _mat.SetFloat("_Anisotropy", 0.62f);
        }

        /// An open cone: apex at the origin, lip one unit below, no cap.
        ///
        /// No cap on purpose — a disc at the bottom is a visible bright
        /// ellipse on the ground, and the light's own pool is already drawing
        /// that far better. Normals point OUTWARD so the rim fade in the
        /// shader has something to measure against.
        static Mesh BuildCone(int segments)
        {
            var verts = new Vector3[segments * 2];
            var norms = new Vector3[segments * 2];
            var uvs = new Vector2[segments * 2];
            var tris = new int[segments * 6];

            for (int i = 0; i < segments; i++)
            {
                float t = i / (float)segments * Mathf.PI * 2f;
                var dir = new Vector3(Mathf.Cos(t), 0, Mathf.Sin(t));
                verts[i] = Vector3.zero;                  // apex, at the bulb
                verts[segments + i] = dir - Vector3.up;   // the lip
                // The side normal of a 45-degree cone, which is what the rim
                // fade reads. Computed rather than approximated as `dir`,
                // because a horizontal normal makes the top of the cone fade
                // wrongly when you look down at it from above — which is
                // exactly where the player's camera usually is.
                var n = new Vector3(dir.x, 1f, dir.z).normalized;
                norms[i] = n;
                norms[segments + i] = n;
                uvs[i] = new Vector2(i / (float)segments, 0f);
                uvs[segments + i] = new Vector2(i / (float)segments, 1f);

                int j = (i + 1) % segments;
                int o = i * 6;
                tris[o + 0] = i;
                tris[o + 1] = segments + i;
                tris[o + 2] = segments + j;
                tris[o + 3] = i;
                tris[o + 4] = segments + j;
                tris[o + 5] = j;
            }

            var mesh = new Mesh { name = "LightShaftCone" };
            mesh.vertices = verts;
            mesh.normals = norms;
            mesh.uv = uvs;
            mesh.triangles = tris;
            // Generous, because the cone is scaled per lamp and a tight bound
            // pops it out of view at the exact moment you walk under it.
            mesh.bounds = new Bounds(new Vector3(0, -0.5f, 0), new Vector3(2.2f, 1.2f, 2.2f));
            return mesh;
        }

        public static int Count => _all.Count;
    }
}
