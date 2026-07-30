using System.Collections.Generic;
using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// THE BRIDGE. `Core/Perception` is engine-free and knows nothing about
    /// where anybody is standing; this is the layer that answers its three
    /// questions from the actual scene — how lit is that spot, is there a wall
    /// in the way, and how loud is it where this person is standing.
    ///
    /// IT ALSO OWNS THE BUDGET. Spec §17.1: only the Near band perceives,
    /// vision recomputes at ~6Hz staggered rather than every frame for
    /// everybody, hearing is event-driven and therefore nearly free, and the
    /// raycast is the LAST test rather than the first because cone, range and
    /// light reject most candidates for nothing.
    public static class Perceivers
    {
        /// Vision recomputes at this rate per walker, spread across frames so
        /// the cost is flat rather than spiky. A head that turns a sixth of a
        /// second late is invisible; sixty cone tests in one frame is not.
        public const float VisionHz = 6f;

        /// Everything above this distance from the player is not evaluated at
        /// all. The Near band is what perceives — the Mid band carries and
        /// passes talk without bodies, which is tested and works, and giving
        /// three thousand residents vision cones would cost the frame budget
        /// and buy nothing the mill does not already produce.
        public const float NearBandMetres = 45f;

        /// Shared hit buffer for `Occluded`. Sixteen is generous for a line
        /// across a street; the overflow case is handled rather than ignored.
        static readonly RaycastHit[] _hits = new RaycastHit[16];

        static readonly List<Light> _lamps = new List<Light>();
        static float _lampsRefreshedAt = -999f;

        /// HOW LIT IS THIS SPOT — the number `LightModel` has been computing
        /// for the renderer for weeks while no NPC ever read it.
        ///
        /// Daylight plus whatever lamps reach, saturating rather than summing
        /// past one: standing under two lamps is not twice as visible as
        /// standing under one, it is just lit.
        public static double LevelAt(Vector3 world)
        {
            double daylight = 1.0 - Mathf.Clamp01(GameController.NightAmount);

            // Lamps do not move, so this only needs to catch the world being
            // built and the odd one being switched. Every five seconds meant a
            // FindObjectsByType over a scene with three hundred and sixty
            // lights twelve times a minute for a list that almost never changes.
            if (Time.time - _lampsRefreshedAt > 20f)
            {
                _lamps.Clear();
                foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                    if (l.enabled && l.type != LightType.Directional) _lamps.Add(l);
                _lampsRefreshedAt = Time.time;
            }

            double lamp = 0;
            foreach (var l in _lamps)
            {
                if (l == null || !l.isActiveAndEnabled) continue;
                float d = Vector3.Distance(l.transform.position, world);
                if (d >= l.range) continue;
                // Linear-ish falloff, deliberately not inverse-square: the
                // renderer's falloff is about how bright a pixel is and this
                // is about whether a person is legible, which holds up much
                // further out than the photometry does.
                double reach = 1.0 - d / l.range;
                lamp = System.Math.Max(lamp, reach * Mathf.Clamp01(l.intensity));
            }

            // Saturating combination. Two lamps and the moon is still "lit".
            return Feel.Clamp01(daylight + lamp - daylight * lamp);
        }

        /// The expensive test, and therefore the last one. Callers must have
        /// already rejected on cone, range and light.
        public static bool Occluded(Vector3 from, Vector3 to)
        {
            Vector3 a = from + Vector3.up * 1.5f, b = to + Vector3.up * 1.5f;
            Vector3 d = b - a;
            float len = d.magnitude;
            if (len < 0.05f) return false;
            // Ignore triggers, and ignore the two bodies themselves — a
            // capsule collider on the subject would otherwise occlude the
            // subject, which is the kind of bug that makes a whole system
            // look mysteriously broken.
            // NON-ALLOCATING, and on this budget that is not a micro-
            // optimisation. This runs up to three times per walker per tick —
            // vision, hearing and the standoff — which at twenty-two walkers
            // and 6Hz is around four hundred raycasts a second. `RaycastAll`
            // returns a fresh array every call, so the allocating version was
            // handing the collector four hundred arrays a second for a system
            // whose whole budget is 1.2ms.
            int n = Physics.RaycastNonAlloc(a, d / len, _hits, len, ~0,
                                            QueryTriggerInteraction.Ignore);
            for (int i = 0; i < n; i++)
            {
                var h = _hits[i];
                if (h.collider == null) continue;
                if (h.collider.GetComponentInParent<NpcWalker>() != null) continue;
                if (h.collider.GetComponentInParent<PlayerController>() != null) continue;
                return true;
            }
            // A full buffer means there may be more hits we did not see. Erring
            // toward OCCLUDED is the safe direction: a missed wall makes the
            // city see through buildings, which is unfair, and a phantom wall
            // only makes somebody miss you.
            return n >= _hits.Length;
        }

        /// THE AMBIENT FLOOR where this person is standing, which is what makes
        /// loudness relative rather than absolute. Built from things the mixer
        /// already knows: the hour, the weather, and how many people are near.
        public static double AmbientFloorAt(Vector3 world, int peopleNearby)
        {
            float night = Mathf.Clamp01(GameController.NightAmount);
            // 3am residential is the quietest the city gets; noon on a street
            // is the default. Interpolated by the same night amount the
            // lighting uses, so the quiet hours and the dark hours agree.
            double floor = Mathf.Lerp((float)Perception.AmbientDaytimeStreet,
                                      (float)Perception.AmbientNight3am, night);
            // A crowd is its own ambient bed, and this is the number that makes
            // the market and the bar into cover.
            floor += Mathf.Clamp(peopleNearby * 1.6f, 0f, 23f);
            if (Weather.Rain > 0.15f)
                floor += Perception.AmbientRainAdds * Mathf.Clamp01(Weather.Rain);
            return floor;
        }

        /// Degrees between where this transform is facing and that point.
        public static double OffAxis(Transform who, Vector3 target)
        {
            Vector3 to = target - who.position; to.y = 0;
            if (to.sqrMagnitude < 1e-4f) return 0;
            Vector3 fwd = who.forward; fwd.y = 0;
            return Vector3.Angle(fwd, to);
        }

        // ---------------------------------------------------------------
        // COUNTERS — what the Phase 1 BEHAVIOUR gate reads
        // ---------------------------------------------------------------
        //
        // The machinery gate asks whether a lit walker is detected further
        // than a shadowed one, which a city that reacts to nothing can pass.
        // These count what actually happened to the player, which it cannot.

        public static int Looks;              // heads that turned toward the player
        public static int Remarks;            // people who said something about it
        public static int LoiterNotices;      // noticed for standing about
        public static int NightRunNotices;    // noticed for running in the dark
        public static int NoiseInvestigations;// walked toward a sound
        public static double PeakHush;        // deepest the street went quiet, 0..1

        public static void ResetCounters()
        {
            Looks = Remarks = LoiterNotices = NightRunNotices = NoiseInvestigations = 0;
            PeakHush = 0;
            // AND THE SOUND STATE, which the first version of this method
            // missed while the perception gate was already reading
            // SoundsEmitted. A reset that clears some of a class's counters is
            // worse than no reset at all, because the ones it forgets look
            // deliberate.
            SoundsEmitted = 0;
            LastSoundTime = -999f;
            LastSoundLoudness = 0;
            LastSoundKind = null;
            _lastRingAt = -999f;
        }

        /// Currently-attending walkers, maintained by `NpcWalker` so the hush
        /// can be computed once per frame rather than per listener.
        public static int Attending;
        public static int PresentNearby;

        public static double Hush => Notice.HushFraction(Attending, PresentNearby);

        // ---------------------------------------------------------------
        // SOUND EVENTS — event-driven, and therefore nearly free
        // ---------------------------------------------------------------
        //
        // Hearing costs nothing per frame. Sounds are rare, so there is no
        // per-listener tick at all: something happens, and the listeners who
        // are near enough find out on their next vision tick. That is the
        // whole reason §17.1 could promise a 1.2ms budget for a system with a
        // second sense in it.
        //
        // ONE SLOT, NOT A QUEUE, and it is a deliberate simplification rather
        // than a shortcut: what matters is the loudest recent thing, because
        // a person turns toward one noise and not toward four. A queue would
        // buy precision nobody can perceive and cost a per-walker cursor.

        /// The noise ring, which can be turned off. It is a teaching device
        /// rather than a HUD, and a player who has learned the model should be
        /// able to stop being told — the same reasoning as the accessibility
        /// marker in §6.2, pointed the other way.
        public static bool RingsEnabled = true;

        /// HOW LIT THE PLAYER IS, computed ONCE PER FRAME.
        ///
        /// `LevelAt` walks every lamp in the scene, and with three hundred and
        /// sixty light shafts that list is long. Every walker was calling it
        /// with the SAME argument — the player's position — on every perception
        /// tick, so twenty-two walkers at 6Hz meant twenty-two identical sweeps
        /// of a few hundred lights, more than a hundred times a second, for one
        /// number.
        ///
        /// It is also the same number `FilmGrade.LitAmount` needs, which makes
        /// caching it here the third instance of the rule this system keeps
        /// running into: one fact, one source. The symmetry rule promises the
        /// player that what they read off the frame and what the city can see
        /// are the same thing, and that can only stay true if there is one of it.
        public static double PlayerLight { get; private set; } = 1.0;
        static int _playerLightFrame = -1;

        public static double RefreshPlayerLight(Vector3 at)
        {
            if (_playerLightFrame == Time.frameCount) return PlayerLight;
            _playerLightFrame = Time.frameCount;
            PlayerLight = LevelAt(at);
            return PlayerLight;
        }

        /// Set once by the game so `Emit` can size the ring against the
        /// player's own ambient floor without every emitter passing it in.
        static Transform _player;
        static float _lastRingAt = -999f;
        public static void BindPlayer(Transform player) => _player = player;

        public static Vector3 LastSoundAt;
        public static double LastSoundLoudness;
        public static string LastSoundKind;
        public static float LastSoundTime = -999f;
        public static int SoundsEmitted;

        /// How long a sound stays worth walking toward. After this it is a
        /// thing that happened rather than a thing happening.
        public const float SoundFreshSeconds = 6f;

        public static void Emit(Vector3 at, double loudness, string kind)
        {
            // A quieter sound does not overwrite a louder one that is still
            // fresh — otherwise a footstep erases a gunshot, which is exactly
            // backwards and is the bug this guard exists for.
            bool fresh = Time.time - LastSoundTime < SoundFreshSeconds;
            if (fresh && loudness < LastSoundLoudness) return;
            LastSoundAt = at;
            LastSoundLoudness = loudness;
            LastSoundKind = kind;
            LastSoundTime = Time.time;
            SoundsEmitted++;

            // AND SHOW IT, once, at the true radius. Drawn here rather than at
            // every call site so no emitter can make a sound the player is not
            // told about — which is the same argument as FilmGrade reading the
            // same LevelAt the NPCs read: one fact, one source.
            // NEVER TWO AT ONCE. Running at night emits a footstep loud
            // enough to draw a ring roughly every half-second, and a stack of
            // overlapping circles is unreadable — which would make the one
            // device teaching the hearing model into the thing obscuring it.
            // One ring at a time, so the newest is always the whole picture.
            if (RingsEnabled && _player != null
                && Time.time - _lastRingAt >= NoiseRing.LifeSeconds)
            {
                _lastRingAt = Time.time;
                bool occluded = Occluded(_player.position, at);
                NoiseRing.Show(at, loudness, occluded,
                               AmbientFloorAt(_player.position, PresentNearby));
            }
        }

        public static bool SoundIsFresh => Time.time - LastSoundTime < SoundFreshSeconds;
    }
}
