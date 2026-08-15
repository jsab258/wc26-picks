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

        /// Whether the gradient skybox is actually in the render settings, so
        /// the camera code can choose Skybox clear flags only when there is a
        /// skybox to clear to. `Shader.Find` is checked rather than trusted —
        /// Resources shaders are always in the player, but the noise ring's
        /// history is four builds of assuming a shader was present.
        public static bool SkyboxLive => _sky != null;
        static Material _sky;

        static readonly int SkyTopId     = Shader.PropertyToID("_SkyColor");
        static readonly int SkyHorizonId = Shader.PropertyToID("_HorizonColor");
        static readonly int SkyGroundId  = Shader.PropertyToID("_GroundColor");

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
            // Shadow distance comes from the graphics preset, floored by
            // nothing — Core/Detail already refuses to take it to zero,
            // because a city with no shadows reads as broken rather than as
            // cheap.
            QualitySettings.shadowCascades = 4;
            QualitySettings.shadowProjection = ShadowProjection.StableFit;
            QualitySettings.shadowResolution = ShadowResolution.High;
            QualitySettings.softParticles = true;

            // THE SKY, 15 Aug. Until now nothing set `RenderSettings.skybox`,
            // so the camera cleared to a flat fog-coloured card and the
            // gradient LightModel computes every frame reached only the
            // ambient trilight. One material, colours written per frame in
            // LateUpdate; the camera flips to Skybox clear in GameController
            // only when `SkyboxLive` says this actually loaded.
            var skyShader = Shader.Find("Hidden/LedgerSky");
            if (skyShader != null)
            {
                _sky = new Material(skyShader) { hideFlags = HideFlags.HideAndDontSave };
                RenderSettings.skybox = _sky;
                // What dry glossy surfaces (windows, glass) reflect. 64 is
                // plenty for a three-colour gradient, and it is what keeps
                // DynamicGI.UpdateEnvironment cheap enough to call while the
                // light moves. Wet ground ignores this: WetReflections
                // publishes its own scene capture as a custom cubemap.
                RenderSettings.defaultReflectionResolution = 64;
            }
            else
            {
                Debug.LogWarning("SceneLighting: Hidden/LedgerSky missing — flat sky fallback");
            }
            ApplyQuality();
        }

        /// Everything the graphics preset controls that lives in Unity's own
        /// quality settings. Public and idempotent so the options screen can
        /// call it the moment the slider moves — a graphics setting that
        /// needs a restart to show anything cannot be tuned against the frame
        /// rate it exists to fix.
        public static void ApplyQuality()
        {
            // Floored by nothing here: Core/Detail already refuses to take
            // shadows to zero, because a city with none reads as broken
            // rather than as cheap.
            QualitySettings.shadowDistance =
                (float)Ledger.Core.Detail.ShadowDistance(
                    Ledger.Core.Detail.Parse(GameSettings.Current.Detail));
            LightShaft.ApplyPreset();
            FilmGrade.ApplyPreset();
            ApplyRenderScale();
        }

        /// THE ONE LEVER A RETINA LAPTOP NEEDS. The post stack is priced per
        /// pixel and is not reduced by the graphics preset at all, so on a
        /// MacBook Air panel (~4.3 million pixels) the preset alone cannot
        /// buy the frame back. 75% is half the pixel cost for a softness
        /// that is hard to spot in motion; 55% is a third.
        ///
        /// The 100% BASELINE IS CAPTURED, not asked of the display: what the
        /// game launched at, in real backbuffer pixels, is what "native"
        /// means on this machine — display-mode queries on macOS disagree
        /// about points versus pixels across Unity versions, and a captured
        /// number cannot. Never in the sim: its stills are rendered into
        /// RenderTextures at fixed sizes, and this must stay a fact about
        /// the player's screen, not about the instrument.
        public static void ApplyRenderScale()
        {
            if (SimMode.Days > 0 || Application.isBatchMode) return;
            if (_baseW == 0) { _baseW = Screen.width; _baseH = Screen.height; }
            int pct = Mathf.Clamp(GameSettings.Current.RenderScalePercent, 50, 100);
            int w = Mathf.Max(960, _baseW * pct / 100);
            int h = Mathf.Max(540, _baseH * pct / 100);
            if (Screen.width == w && Screen.height == h) return;
            Screen.SetResolution(w, h, Screen.fullScreenMode);
        }
        static int _baseW, _baseH;

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

            if (_sky != null)
            {
                // The horizon stop is the FOG colour, deliberately — the
                // skybox is not fogged, so any other choice puts a seam where
                // fogged geometry meets sky. The shader comment carries the
                // full argument.
                _sky.SetColor(SkyTopId, C(LightModel.SkyColour(night, rain)));
                _sky.SetColor(SkyHorizonId, RenderSettings.fogColor);
                _sky.SetColor(SkyGroundId, C(LightModel.GroundColour(night, rain)));

                // What a DRY window reflects only updates when this is called
                // — assigning `RenderSettings.skybox` refreshes nothing on
                // its own. Thresholded because it re-renders the environment
                // cubemap: night drifts continuously, so ~0.04 steps make a
                // full dusk about two dozen small (64px) refreshes rather
                // than one per frame. Wet ground never waits on this;
                // WetReflections publishes its own capture.
                if (Mathf.Abs(night - _envNight) > 0.04f
                    || Mathf.Abs(rain - _envRain) > 0.25f)
                {
                    _envNight = night;
                    _envRain = rain;
                    DynamicGI.UpdateEnvironment();
                }
            }

            // FALLBACK ONLY (shader missing): the camera stays on SolidColor
            // and its background is the fog colour, so the far end of the
            // street still dissolves without a seam — just into a flat card.
            var cam = Camera.main;
            if (cam != null && cam.clearFlags == CameraClearFlags.SolidColor)
                cam.backgroundColor = RenderSettings.fogColor;
        }
        float _envNight = -10f, _envRain = -10f;
    }
}
