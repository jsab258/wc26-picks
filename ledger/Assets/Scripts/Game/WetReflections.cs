using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// WET-SURFACE REFLECTIONS — one probe, moved rarely (the-gap.md §3a).
    ///
    /// The lighting pass got the road to go dark and glossy in the rain, but
    /// glossy with nothing to reflect is just darker asphalt. The thing that
    /// actually sells a wet street at night is the smeared column of a
    /// streetlight lying on it, and that needs a reflection probe.
    ///
    /// THE COST PROBLEM, and the reason this class exists rather than a probe
    /// dropped in a scene: a realtime probe re-rendering every frame is six
    /// extra camera passes a frame, which is the single most expensive thing
    /// this project could switch on. So it is gated twice —
    ///
    ///   1. On whether there is anything to see at all. `ReflectionStrength`
    ///      returns zero for a dry road, and a dry road pays nothing: the
    ///      probe is disabled outright, not rendered-and-faded.
    ///
    ///   2. On DISTANCE TRAVELLED rather than on a timer. A player standing
    ///      still is looking at a reflection that is already correct and will
    ///      stay correct; refreshing it on a timer pays every second for a
    ///      result identical to the one already on screen. A seconds floor
    ///      catches the one case distance misses — a player spinning on the
    ///      spot, who covers no ground and changes the entire view.
    ///
    /// Both rules live in `Core/LightModel` where they are tested. This class
    /// does no maths; like `SceneLighting`, it is a wire.
    public class WetReflections : MonoBehaviour
    {
        static WetReflections _instance;

        /// How many times the probe has actually been re-rendered. The sim
        /// gate reads this: a model that computes a beautiful refresh
        /// schedule nothing ever runs is the same defect as a set-dressing
        /// model that places nothing.
        public static int Refreshes { get; private set; }
        /// Current strength, 0 when the street is dry. Also read by the gate.
        public static float Strength { get; private set; }

        public static void Ensure(Transform follow)
        {
            if (_instance != null) { _instance._follow = follow; return; }
            var go = new GameObject("WetReflections");
            _instance = go.AddComponent<WetReflections>();
            _instance._follow = follow;
            _instance.Build();
        }

        Transform _follow;
        ReflectionProbe _probe;
        Vector3 _lastRenderedAt;
        float _metresSince, _secondsSince;

        /// How high above the player the probe sits. Roughly head height of a
        /// standing figure rather than ground level: a probe ON the road
        /// captures the road's own underside in half its faces.
        const float ProbeHeight = 2.2f;

        void Build()
        {
            _probe = gameObject.AddComponent<ReflectionProbe>();
            _probe.mode = UnityEngine.Rendering.ReflectionProbeMode.Realtime;
            // ViaScripting, never OnAwake or EveryFrame — the whole design is
            // that WE decide when, from the model.
            _probe.refreshMode = UnityEngine.Rendering.ReflectionProbeRefreshMode.ViaScripting;
            // Spread the six faces across six frames. One face a frame is
            // invisible in a reflection this blurred, and it turns a spike
            // into a slope.
            _probe.timeSlicingMode = UnityEngine.Rendering.ReflectionProbeTimeSlicingMode.IndividualFaces;

            // Low. A wet road is a BLURRED mirror — every pixel past about
            // this is spent on detail the surface roughness immediately
            // throws away.
            _probe.resolution = 64;
            _probe.hdr = true;
            _probe.shadowDistance = 25f;
            _probe.farClipPlane = 60f;
            _probe.nearClipPlane = 0.3f;

            // Box projection, so the reflection is parallax-corrected against
            // the street rather than treated as infinitely far away. Without
            // it a streetlight's reflection sits at the horizon instead of on
            // the road under the lamp, which is worse than no reflection —
            // it reads as a rendering error rather than as wet ground.
            _probe.boxProjection = true;
            _probe.size = new Vector3(48f, 18f, 48f);
            _probe.center = Vector3.zero;

            // Only the things worth reflecting. Reflecting the player is both
            // wrong (they are inside the probe) and expensive.
            _probe.cullingMask = ~0;

            _probe.enabled = false;
            _lastRenderedAt = new Vector3(float.NaN, 0, 0);
        }

        /// A/B switch for the sim, and a PROPERTY so it applies on the spot.
        /// The light-shaft version of this was a plain field read by
        /// LateUpdate, which meant a probe that set it false and true inside
        /// one Update never disabled anything and cheerfully reported that
        /// the shafts contributed nothing.
        public static bool Enabled
        {
            get => _enabled;
            set
            {
                if (_enabled == value) return;
                _enabled = value;
                if (_instance == null || _instance._probe == null) return;
                if (!value)
                {
                    // BOTH, and the intensity is the one that matters.
                    // Disabling a realtime probe stops it UPDATING; the
                    // renderers keep sampling the cubemap it last produced,
                    // so `enabled = false` alone can leave the reflection
                    // fully in the frame and report that the probe
                    // contributes nothing. That is the third time tonight an
                    // A/B has measured its own inertness and called it a
                    // result.
                    _instance._probe.intensity = 0f;
                    _instance._probe.enabled = false;
                }
                else
                {
                    _instance._probe.enabled = true;
                    _instance._probe.intensity = Strength;
                }
            }
        }
        static bool _enabled = true;

        void LateUpdate()
        {
            if (_probe == null) return;
            if (!_enabled) { _probe.enabled = false; return; }

            Strength = Ledger.Core.Detail.Reflections(
                          Ledger.Core.Detail.Parse(GameSettings.Current.Detail))
                ? (float)LightModel.ReflectionStrength(
                      SceneLighting.Wetness, GameController.NightAmount)
                : 0f;

            if (Strength <= 0f)
            {
                // Dry. Off completely — not rendered at zero intensity, which
                // would pay the full cost for a result multiplied away.
                if (_probe.enabled)
                {
                    _probe.enabled = false;
                    _lastRenderedAt = new Vector3(float.NaN, 0, 0);
                }
                _metresSince = _secondsSince = 0f;
                return;
            }

            _probe.enabled = true;
            _probe.intensity = Strength;

            Vector3 want = _follow != null
                ? _follow.position + Vector3.up * ProbeHeight
                : transform.position;

            if (float.IsNaN(_lastRenderedAt.x))
            {
                // First frame wet: render where we stand, immediately.
                Render(want);
                return;
            }

            _secondsSince += Time.deltaTime;
            _metresSince = Vector3.Distance(want, _lastRenderedAt);

            if (LightModel.ShouldRefreshReflection(_metresSince, _secondsSince, Strength))
                Render(want);
        }

        /// The probe MOVES only when it re-renders, and this is the part that
        /// is easy to get wrong: dragging it along with the player every
        /// frame while the cubemap is stale makes the box projection
        /// re-project an old capture from a new origin, and the reflection
        /// visibly slides across the road as you walk. Held still between
        /// refreshes it is merely out of date, which at this blur is
        /// invisible; moved continuously it is out of date AND sliding,
        /// which is not.
        void Render(Vector3 at)
        {
            transform.position = at;
            _lastRenderedAt = at;
            _metresSince = _secondsSince = 0f;
            _probe.RenderProbe();
            Refreshes++;
        }
    }
}
