using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// ONE RING, ONE MOMENT — `weapons-spec.md` §6.2.
    ///
    /// The hearing model is the most counter-intuitive thing in this game: a
    /// sound is not loud or quiet in the abstract, it is loud or quiet
    /// *relative to what is already happening where the listener is standing*.
    /// A suppressed pistol carries nothing in a busy bar and eighty-six metres
    /// in a residential street at three in the morning. Nobody will guess that,
    /// and there is no HUD to tell them.
    ///
    /// So at the instant a sound is made, a single ring on the ground at the
    /// TRUE audible radius — after occlusion and after masking — and then it is
    /// gone. Not a persistent overlay, not a meter. It teaches the model in
    /// three or four uses and then the player stops needing it, which is the
    /// mark of good feedback rather than of a lot of feedback.
    ///
    /// WHY IT IS DRAWN AND NOT WRITTEN. A number in a corner would be more
    /// precise and would tell the player nothing they could act on. A circle
    /// around their own feet, the size of the problem they just made, is
    /// spatial information delivered spatially.
    public class NoiseRing : MonoBehaviour
    {
        /// How long the ring is on screen. Long enough to read at a glance,
        /// short enough that it never becomes scenery.
        public const float LifeSeconds = 0.55f;

        /// Below this the ring is not worth drawing — a footstep that carries
        /// three metres in a silent street is real and true and a circle round
        /// your own shoes is noise on the screen.
        public const double MinRadiusMetres = 6.0;

        const int Segments = 64;

        static Material _mat;
        float _born;
        float _radius;
        LineRenderer _line;

        /// Draw the ring for a sound of this loudness at this place, sized by
        /// the ambient floor where the PLAYER is standing.
        ///
        /// The player's floor rather than some average: the ring answers "how
        /// far did that carry, for somebody like me, here", which is the
        /// question a player is actually asking. An average over the whole
        /// street would be more defensible and less useful.
        public static void Show(Vector3 at, double loudness, bool occluded,
                                double ambientFloorAtPlayer)
        {
            double r = Perception.AudibleRadius(loudness, ambientFloorAtPlayer, occluded);
            if (r < MinRadiusMetres) return;

            var go = new GameObject("NoiseRing");
            go.transform.position = at + Vector3.up * 0.04f;   // just off the road
            var ring = go.AddComponent<NoiseRing>();
            ring._radius = (float)r;
            ring._born = Time.time;
            ring.Build();
        }

        void Build()
        {
            _line = gameObject.AddComponent<LineRenderer>();
            _line.useWorldSpace = false;
            _line.loop = true;
            _line.positionCount = Segments;
            // Thickness scales with the ring, or a district-sized circle is a
            // hairline and a room-sized one is a doughnut.
            _line.widthMultiplier = Mathf.Clamp(_radius * 0.012f, 0.05f, 0.5f);
            _line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _line.receiveShadows = false;
            _line.alignment = LineAlignment.TransformZ;

            if (_mat == null)
            {
                // Unlit and additive: it reads on wet asphalt at night, which
                // is the surface it will nearly always be drawn on, and it
                // cannot pick up the lamp specular the road has.
                var shader = Shader.Find("Sprites/Default") ?? Shader.Find("Unlit/Color");
                _mat = new Material(shader);
            }
            _line.material = _mat;

            for (int i = 0; i < Segments; i++)
            {
                float a = i / (float)Segments * Mathf.PI * 2f;
                _line.SetPosition(i, new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * _radius);
            }
            // Flat on the ground rather than standing up like a hoop.
            transform.rotation = Quaternion.Euler(90, 0, 0);
        }

        void Update()
        {
            float t = (Time.time - _born) / LifeSeconds;
            if (t >= 1f) { Destroy(gameObject); return; }

            // IT DOES NOT EXPAND. An expanding ring reads as a shockwave and
            // invites the player to watch it travel, which is a lie — the
            // radius is the answer, not the animation. It arrives at full size
            // and fades, so the size is the only thing carrying information.
            float alpha = 1f - t * t;
            var c = new Color(0.85f, 0.88f, 0.95f, alpha * 0.55f);
            _line.startColor = c;
            _line.endColor = c;
        }
    }
}
