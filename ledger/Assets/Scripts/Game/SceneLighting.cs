using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The render settings authority (the-gap.md §3a).
    ///
    /// Nothing in this project has a scene file, so nothing has ever set
    /// Unity's lighting defaults — which means the game has been shipping
    /// with a flat trilight ambient, no fog at all, and Unity's landscape
    /// shadow distance spent on ground the player never looks at.
    ///
    /// Every value here comes from `Core/LightModel`, which is where the
    /// curves live and where they are tested. This class does no maths; it
    /// is a wire.
    ///
    /// Runs every frame rather than on a change, deliberately: night is
    /// continuous now, rain moves, and a lighting rig that only updates on a
    /// threshold is how you get the hard cut at 20:00 the ambience beds used
    /// to have.
    public class SceneLighting : MonoBehaviour
    {
        static SceneLighting _instance;

        public static void Ensure()
        {
            if (_instance != null) return;
            var go = new GameObject("SceneLighting");
            _instance = go.AddComponent<SceneLighting>();
            _instance.ApplyOnce();
        }

        /// How wet the ground currently is — lags the rain in both
        /// directions, so the street still looks rained-on afterwards.
        public static float Wetness { get; private set; }

        static Color C((double r, double g, double b) c) =>
            new Color((float)c.r, (float)c.g, (float)c.b, 1f);

        void ApplyOnce()
        {
            // Three-band ambient. One flat colour for all three is the thing
            // that makes untextured geometry look untextured.
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;

            RenderSettings.fog = true;
            // Exponential squared: thickens with distance far more gently
            // near the camera, which is what keeps the street readable while
            // still hiding the edge of the world.
            RenderSettings.fogMode = FogMode.ExponentialSquared;

            // A street, not a landscape. Unity's default spends the cascade
            // budget on ground nobody looks at and leaves soft mush on the
            // person standing three metres away.
            QualitySettings.shadowDistance = (float)LightModel.ShadowDistanceMetres;
            QualitySettings.shadowCascades = 4;
            QualitySettings.shadowProjection = ShadowProjection.StableFit;
            QualitySettings.shadowResolution = ShadowResolution.High;
            QualitySettings.softParticles = true;
        }

        void LateUpdate()
        {
            float night = GameController.NightAmount;
            float rain = Weather.Rain;

            Wetness = (float)LightModel.Wetness(Wetness, rain, Time.deltaTime);
            AssetLibrary.SetWetness(Wetness);

            RenderSettings.ambientSkyColor = C(LightModel.SkyColour(night, rain));
            RenderSettings.ambientEquatorColor = C(LightModel.HorizonColour(night, rain));
            RenderSettings.ambientGroundColor = C(LightModel.GroundColour(night, rain));

            RenderSettings.fogColor = C(LightModel.FogColour(night, rain));
            RenderSettings.fogDensity = (float)LightModel.FogDensity(night, rain);

            // The camera's background is the fog colour, so the far end of
            // the street dissolves into the sky instead of ending at a seam.
            var cam = Camera.main;
            if (cam != null && cam.clearFlags == CameraClearFlags.SolidColor)
                cam.backgroundColor = RenderSettings.fogColor;
        }
    }
}
