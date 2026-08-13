using UnityEngine;

namespace Ledger.Game
{
    /// ART DIRECTION: STYLISED NOIR (approved 2026-07-28, with the standing
    /// note that it "can't be too depressing, has to make the player come
    /// back"). Weather is the single highest-leverage tool we have, because
    /// it does three jobs at once and all of them are cheap:
    ///
    ///   - ART: wet asphalt under a sodium lamp is the whole look. Rain plus
    ///     neon reflections reads as INVITING rather than bleak, which is the
    ///     answer to the not-too-depressing note. Nobody thinks of Blade
    ///     Runner's street level as a downer; it is the most seductive wet
    ///     pavement ever filmed.
    ///   - PERFORMANCE: fog pulls the far plane in, so we draw less.
    ///   - BUDGET: it hides low-detail geometry, which is exactly what a
    ///     project with a $200 asset budget needs it to do.
    ///
    /// It is also a mechanic in waiting: rain thins the crowd, quiets the
    /// street, and gives a coat a reason to be up — all of which the gossip
    /// and stance systems already understand.
    public class Weather : MonoBehaviour
    {
        /// 0 = dry, 1 = pouring. Drives puddles, reflections, sound, and how
        /// far you can see.
        public static float Rain { get; private set; }
        /// Surfaces stay wet AFTER the rain stops, which is when the city
        /// looks its best and is the reason to model wetness separately.
        public static float Wetness { get; private set; }

        static Weather _instance;
        static Material _asphalt, _concrete;
        static float _dryAsphaltSmooth, _dryConcreteSmooth;
        ParticleSystem _rainFx;
        GameController _game;
        int _decidedForDay = -1;
        float _targetRain;

        public static void Ensure(GameController game)
        {
            if (_instance != null) return;
            var go = new GameObject("Weather");
            _instance = go.AddComponent<Weather>();
            _instance._game = game;
            _instance.Build();
        }

        void Build()
        {
            // Cache the dry values ONCE. Reading them back after we have
            // already wetted the material would bake the rain in permanently.
            _asphalt = AssetLibrary.Material(AssetLibrary.Asphalt);
            _concrete = AssetLibrary.Material(AssetLibrary.Concrete);
            if (_asphalt != null) _dryAsphaltSmooth = _asphalt.GetFloat("_Glossiness");
            if (_concrete != null) _dryConcreteSmooth = _concrete.GetFloat("_Glossiness");

            // Rain as a particle system that follows the camera — a box of
            // falling streaks is indistinguishable from real rain at street
            // level and costs nothing.
            var fx = new GameObject("RainFX");
            fx.transform.SetParent(transform, false);
            _rainFx = fx.AddComponent<ParticleSystem>();
            var main = _rainFx.main;
            main.startLifetime = 1.1f;
            main.startSpeed = 26f;
            main.startSize = 0.06f;
            main.startColor = new Color(0.75f, 0.8f, 0.9f, 0.45f);
            main.maxParticles = 3000;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.gravityModifier = 1.4f;

            var shape = _rainFx.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(38f, 0.2f, 38f);

            var emission = _rainFx.emission;
            emission.rateOverTime = 0f;      // driven by Rain below

            var renderer = fx.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Stretch;
            renderer.velocityScale = 0.06f;
            renderer.lengthScale = 3.5f;
            // SPRITES/DEFAULT, NOT THE GLASS SHEET. Glass is a lit opaque
            // surface material for WINDOWS; on stretched particles it
            // ignores the translucent startColor above and renders every
            // drop as a dark streak — the first player-height still
            // (review_street, dfefd62) has a sky full of black scratches
            // that no elevated frame ever showed, because from above the
            // drops sat against dark ground. The unlit sprite shader reads
            // the vertex colour and its alpha, which is what the pale
            // 0.45-alpha streak was always meant to be.
            renderer.material = new Material(Shader.Find("Sprites/Default"));
            _rainFx.Play();
        }

        void Update()
        {
            if (_game == null) return;

            // One decision a day, so weather is a THING THAT HAPPENED rather
            // than a flicker. Seeded off the day so a reloaded save gets the
            // same sky it had.
            if (_decidedForDay != _game.Now.Day)
            {
                _decidedForDay = _game.Now.Day;
                var rng = new System.Random(_game.Now.Day * 7717 + 3);
                double roll = rng.NextDouble();
                // Mostly clear, sometimes drizzle, occasionally a real
                // downpour. A city that rains every day is a city nobody
                // wants to come back to.
                _targetRain = roll < 0.55f ? 0f
                            : roll < 0.85f ? 0.35f
                            : 0.9f;
            }

            Rain = Mathf.MoveTowards(Rain, _targetRain, Time.deltaTime * 0.08f);
            // Wetness lags rain in both directions: it takes a while to soak,
            // and much longer to dry. The look lives in that tail.
            float dryRate = Rain > 0.05f ? 0.25f : 0.012f;
            Wetness = Mathf.MoveTowards(Wetness, Rain > 0.05f ? 1f : 0f, Time.deltaTime * dryRate);

            // Rain follows the player, above head height.
            var cam = Camera.main;
            if (cam != null)
                transform.position = cam.transform.position + Vector3.up * 14f;
            if (_rainFx != null)
            {
                var em = _rainFx.emission;
                em.rateOverTime = Rain * 2200f;
            }

            // AND YOU CAN HEAR IT. The art pass shipped a downpour you could
            // only see, which is worse than no rain at all: the eye and the
            // ear disagree and the ear wins, so the scene reads as footage
            // playing behind glass. Indoors ducks it, because the clearest
            // signal that you have stepped inside is that the weather gets
            // quieter.
            // THE ROOM IS ASKED BY `Audio.Rain` ITSELF NOW. This line passed
            // 0.8 into a method that multiplied it by 0.72, giving 0.424 where
            // `Acoustics.OutsideBleed` says 0.28 — one idea, two
            // implementations, and a shipped value that was the arithmetic of
            // both colliding.
            Audio.Rain(Rain);

            ApplyWetness();
        }

        /// The whole trick: wet asphalt is SHINY asphalt. One float per
        /// material and the street starts holding the lamps.
        static void ApplyWetness()
        {
            if (_asphalt != null)
                _asphalt.SetFloat("_Glossiness", Mathf.Lerp(_dryAsphaltSmooth, 0.82f, Wetness));
            if (_concrete != null)
                _concrete.SetFloat("_Glossiness", Mathf.Lerp(_dryConcreteSmooth, 0.55f, Wetness));
        }

        /// How much the weather closes the world in — read by the lighting
        /// driver so fog, rain and time of day are one decision.
        public static float FogTightness => Mathf.Clamp01(Rain * 0.8f);
    }
}
