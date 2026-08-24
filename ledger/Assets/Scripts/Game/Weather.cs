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
        ParticleSystem _rainFx;
        GameController _game;
        int _decidedForDay = -1;
        float _targetRain;
        static float _forcedRain = -1f;

        /// THE WEATHER PLANT (rule 5b's corollary: plant the condition, never
        /// wait for a lucky run). The daily roll is seeded off the day number,
        /// so the review days 1 and 2 are pinned dry on every run there will
        /// ever be — both open rain findings were waiting on a wet frame the
        /// seed structurally cannot produce. A diagnostic still needs the
        /// STATE, not the transition, so forcing SNAPS Rain and Wetness
        /// instead of ramping them; a negative clears the pin and snaps back
        /// to the day's own rolled target, so the 23:00 night gates measure
        /// the street the seed chose, not the plant's leftovers.
        public static void ForceRain(float target)
        {
            _forcedRain = target;
            float snap = target >= 0f ? target
                       : _instance != null ? _instance._targetRain : 0f;
            Rain = snap;
            Wetness = snap > 0.05f ? 1f : 0f;
        }

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

            // Rain as a particle system that follows the camera — a box of
            // falling streaks is indistinguishable from real rain at street
            // level and costs nothing.
            var fx = new GameObject("RainFX");
            fx.transform.SetParent(transform, false);
            // POINTED DOWN, AND THAT ONE LINE IS THE WHOLE BUG. A Box shape
            // emits along the shape's FORWARD, and nothing here ever rotated
            // it — so world +Z it was, and the rain was being THROWN
            // SIDEWAYS at street level rather than falling.
            //
            // The arithmetic, from the shipped numbers: the sheet sits 14m
            // above the camera, a drop lives 1.1s, and at 1.4x gravity it
            // falls 8.3m in that time while travelling 28.6m horizontally.
            // So a drop DIES 5.7m OVER YOUR HEAD, every time, and not one of
            // them can reach eye level. Measured off two landed frames
            // before the code was read, with hue separating streaks from the
            // sodium glow: bright desaturated pixels read 6.5% and 10.7% in
            // the top third and 0.00-0.26% everywhere below it, in two
            // different frames from two different cameras. The single wedge
            // they occupy is the same fault seen sideways — every drop flies
            // the same WORLD direction, so which part of the frame gets the
            // rain depends on where the camera happens to be looking.
            //
            // The item this closes was called "RAIN AT EYE LEVEL" and was
            // closed on "landed wet frames read as streaks in lamp cones".
            // They do. The lamp cones are above the lamps.
            fx.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            _rainFx = fx.AddComponent<ParticleSystem>();
            var main = _rainFx.main;
            main.startLifetime = 1.1f;
            // 9 m/s, NOT THE 26 THAT WAS HERE — and this is a rename as much
            // as a retune. 26 was a horizontal THROW speed; pointing the
            // emitter down changes what the number means, which is the trap
            // where an instrument keeps its name after its question moves.
            // Rain reaches terminal velocity at roughly 5-9 m/s, gravity
            // adds the rest over the fall, and 26 straight down would read
            // as tracer fire rather than weather. Judge it on `rainLowest`
            // and the wet frame, and retune from the landed series.
            main.startSpeed = 9f;
            // 0.06 -> 0.010, AND THE OLD SIZE WAS ONLY EVER INVISIBLE.
            //
            // Measured off `review_street.jpg` the moment the emitter was
            // pointed down: rain streaks read a MEDIAN 10 PIXELS WIDE and
            // bright-desaturated pixels covered 18.2% of the whole frame,
            // against 6.5% in the top third alone before. That is not
            // weather, it is white bars falling past the lens.
            //
            // The size never changed; what changed is that the drops now
            // come near the camera. Thrown sideways at 26m/s they died 5.7m
            // overhead and 28m out, where a 6cm drop subtends nothing. Fall
            // them through the lens and 6cm at half a metre is a bar. A real
            // raindrop is about 2mm, so 6cm was two orders out and hidden by
            // a second fault the whole time — the fix did not cause this, it
            // uncovered it.
            //
            // The factor comes from the measurement, not from taste: ten
            // pixels median wants one or two, so six times thinner, and 0.010
            // is that with a little left over for a drop being a smear rather
            // than a line. Judge it the same way it was caught — the median
            // run width of bright desaturated pixels on the committed still.
            main.startSize = 0.010f;
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

        /// WHERE THE RAIN ACTUALLY IS, relative to the eye that is meant to
        /// be standing in it.
        ///
        /// `rainLowest` is the height of the LOWEST live drop above the
        /// camera, in metres, and it is the number that would have caught
        /// the sideways emitter on the day it shipped: as built it could not
        /// go below +5.7m however hard it rained, and a positive reading
        /// here means the weather is happening over your head. `rainBelow`
        /// is how many drops are under eye height at all, against
        /// `rainAlive` — rule 3b's denominator, because zero drops below the
        /// eye and no rain today produce the same zero otherwise.
        ///
        /// A MINIMUM AND A COUNT, NOT A MEDIAN, deliberately: "is ANY of it
        /// down here" is not a median question, and a median over a column
        /// of falling rain describes the middle of the column, which is
        /// exactly the part that was never in doubt.
        public static float RainLowest = 999f;
        public static int RainAlive, RainBelow;
        static ParticleSystem.Particle[] _rainBuf;
        int _rainSampleTick;

        void SampleRain()
        {
            if (_rainFx == null || Rain <= 0.05f) return;
            // Every thirtieth frame: `GetParticles` copies the whole buffer
            // and this is a diagnostic, not a mechanic.
            if (++_rainSampleTick % 30 != 0) return;
            var cam = Camera.main;
            if (cam == null) return;
            int cap = _rainFx.main.maxParticles;
            if (_rainBuf == null || _rainBuf.Length < cap)
                _rainBuf = new ParticleSystem.Particle[cap];
            int n = _rainFx.GetParticles(_rainBuf);
            RainAlive = n;
            int below = 0;
            float camY = cam.transform.position.y;
            for (int i = 0; i < n; i++)
            {
                float dy = _rainBuf[i].position.y - camY;
                if (dy < RainLowest) RainLowest = dy;
                if (dy < 0f) below++;
            }
            RainBelow = below;
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

            float goal = _forcedRain >= 0f ? _forcedRain : _targetRain;
            Rain = Mathf.MoveTowards(Rain, goal, Time.deltaTime * 0.08f);
            // Wetness lags rain in both directions: it takes a while to soak,
            // and much longer to dry. The look lives in that tail.
            float dryRate = Rain > 0.05f ? 0.25f : 0.012f;
            Wetness = Mathf.MoveTowards(Wetness, Rain > 0.05f ? 1f : 0f, Time.deltaTime * dryRate);

            // Rain sits over what the camera LOOKS AT, not over its head.
            // The Hook tour frame caught the difference: the tour camera is
            // 14m up and 34m back, so a box anchored above the CAMERA hung
            // in the upper middle of the frame as a scribble cloud behind
            // the street it was supposed to be raining on. Twelve metres
            // down the flattened view direction centres the 38m box over
            // the scene for every vantage this game actually uses; at
            // street level the player is still comfortably inside it.
            var cam = Camera.main;
            float coverage = 1f;
            if (cam != null)
            {
                var fwd = cam.transform.forward; fwd.y = 0;
                if (fwd.sqrMagnitude > 0.01f) fwd.Normalize(); else fwd = Vector3.zero;
                // AND THE FIELD GROWS WITH THE CAMERA'S HEIGHT. The first wet
                // tour frame (the Hook, build R) showed why a fixed box
                // cannot serve two vantages: at street level 38m surrounds
                // the player completely, and from 14m up the same box is a
                // swarm patch in one corner of a view that sees sixty. The
                // box widens with height — about 2.3x at the tour's 14m —
                // and the rate rises LINEARLY with it, not with area, so an
                // elevated view gets a thinner field that covers the frame:
                // which is also what height does to real rain, the far half
                // of a downpour being mostly haze.
                float hi = Mathf.Max(0f, cam.transform.position.y - 2f);
                coverage = Mathf.Clamp(1f + hi * 0.11f, 1f, 2.5f);
                transform.position = cam.transform.position
                    + fwd * (12f * coverage) + Vector3.up * 14f;
                if (_rainFx != null)
                {
                    var shape = _rainFx.shape;
                    shape.scale = new Vector3(38f * coverage, 0.2f, 38f * coverage);
                }
            }
            SampleRain();
            if (_rainFx != null)
            {
                var em = _rainFx.emission;
                em.rateOverTime = Rain * 2200f * coverage;
                var main2 = _rainFx.main;
                main2.maxParticles = Mathf.RoundToInt(3000 * coverage);
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

        }

        /// WET ASPHALT IS SHINY ASPHALT, AND THIS IS NO LONGER WHERE THAT
        /// HAPPENS — the two lines that used to live here had stopped
        /// working and nothing said so.
        ///
        /// They wrote `_Glossiness` straight onto the shared asphalt and
        /// concrete materials. Since gloss MAPS were bound to every textured
        /// surface, `_METALLICGLOSSMAP` is enabled on both, and the Standard
        /// shader IGNORES `_Glossiness` entirely when it is — smoothness
        /// comes from the map's alpha times `_GlossMapScale` instead. So
        /// this ran every frame, cost two writes, and changed nothing.
        ///
        /// `AssetLibrary.SetWetness` is the one implementation, it covers
        /// asphalt, sidewalk, kerb and concrete (`WetSurfaces`), and it goes
        /// through `SetSmoothness`, which knows about the map and scales it
        /// normalised by the map's own mean so the calibrated level holds.
        /// `SceneLighting.LateUpdate` calls it every frame with the same
        /// `Wetness` this class computes.
        ///
        /// Checked before deleting rather than after (rule 5): both surfaces
        /// are in `WetSurfaces`, so nothing is lost with these lines.

        /// How much the weather closes the world in — read by the lighting
        /// driver so fog, rain and time of day are one decision.
        public static float FogTightness => Mathf.Clamp01(Rain * 0.8f);
    }
}
