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

        const int Segments = 64;

        /// The last ring's radius and the loudness it came from, so the sim can
        /// assert the DRAWN circle equals the MODEL's radius rather than
        /// trusting that it does. The lesson behind this is `scoreAudible`: the
        /// way to check a derived number is to compare it against the thing it
        /// derives from, never against a constant typed out a second time.
        public static double LastRadius = -1;
        public static double LastLoudness = -1;
        public static double LastFloor = -1;
        public static bool LastOccluded;
        /// How many rings were SIZED (the model ran) and how many were actually
        /// DRAWN. The first green build reported six hundred and sixty sized
        /// and NONE drawn, and I read that as "the shader was stripped from the
        /// build" — which was a guess, and the wrong one.
        ///
        /// SO THE GAP IS NOW ITEMISED. Three different things stop a ring, they
        /// mean three completely different things, and a single `Shown` counter
        /// cannot tell them apart:
        ///   - too small to be worth drawing — the model working correctly;
        ///   - shadowed by a ring already on the ground — a presentation rule;
        ///   - no material — a broken build.
        /// One number that three causes collapse into is not a measurement, and
        /// this project has now lost two cycles to exactly that shape.
        public static int Sized;
        public static int Shown;
        public static int SkippedSmall;
        public static int SkippedShadowed;
        public static int SkippedNoMaterial;
        /// The largest radius any sound in the run produced. If this is under
        /// `Perception.RingMinRadiusMetres` then nothing loud enough to draw ever
        /// happened and
        /// `Shown == 0` is not a bug at all — which was, in fact, the answer.
        public static double MaxRadius = -1;
        public static string LastSkip = "none";

        static Material _mat;
        static bool _matTried;

        /// SHADER LOOKUP CAN FAIL IN A BUILT PLAYER, and that is the whole
        /// reason this is a function with a guard rather than two lines in
        /// `Build`. A shader no material in any scene references gets stripped
        /// from the build, `Shader.Find` returns null, and `new Material(null)`
        /// throws — which for this class would mean an exception on every sound
        /// the game makes. The editor would never show it.
        ///
        /// So: try once, and if there is nothing to draw with, draw nothing.
        /// A missing ring is a missing teaching aid; an exception per footstep
        /// is a broken game.
        static Material Mat()
        {
            if (_matTried) return _mat;
            _matTried = true;
            var shader = Shader.Find("Sprites/Default")
                         ?? Shader.Find("Unlit/Color")
                         ?? Shader.Find("Legacy Shaders/Particles/Alpha Blended");
            if (shader != null) _mat = new Material(shader);
            return _mat;
        }

        // ---------------------------------------------------------------
        // ONE RING AT A TIME, BUT THE LOUDEST ONE — the bug that made the
        // whole device invisible
        // ---------------------------------------------------------------
        //
        // The first version rate-limited rings in `Perceivers.Emit`: at most one
        // every `LifeSeconds`, whatever it was for. That is the correct
        // INTENTION — overlapping circles are unreadable — and the wrong rule,
        // because it is blind to which sound matters.
        //
        // Walking emits a footstep every stride, which in a CI frame of nearly
        // three hundred milliseconds is about once a frame. Every other frame
        // one of those sized a ring, so at any instant there was a ring's-worth of cooldown
        // standing between the player and the next circle. A door slam, a
        // smashed bottle, a gunshot — the sounds the ring EXISTS to explain —
        // then had a coin-flip chance of arriving inside a footstep's shadow and
        // being thrown away. Across a thirteen-day CI run the one slam lost that
        // flip, six hundred and sixty footsteps sized rings that were all far
        // too small to draw, and the counter said zero.
        //
        // So the cooldown now tracks what was DRAWN, not what was measured, and
        // a meaningfully louder sound preempts it and replaces the circle on the
        // ground. A footstep can never block a gunshot. That is the rule the
        // comment always claimed — "the newest is always the whole picture" —
        // and it should have said the LOUDEST.

        // THE NUMBERS AND THE RULE BOTH LIVE IN `Perception` NOW —
        // `RingMinRadiusMetres`, `RingPreemptBy`, `RingRepeatQuietSeconds` and
        // `RingDraw`. They were here, in the layer nothing local compiles, which
        // is why a rule that discarded every ring worth drawing survived a green
        // build. Forwarding aliases were the first instinct and are the same
        // mistake one step smaller: one fact, one name.

        static float _shownAt = -999f;
        static double _shownLoudness = -1;
        static NoiseRing _live;

        /// Zeroed with the rest of the perception counters at the start of a
        /// sim run, so the numbers in the verdict describe THIS run.
        public static void Reset()
        {
            Sized = Shown = SkippedSmall = SkippedShadowed = SkippedNoMaterial = 0;
            MaxRadius = -1;
            LastRadius = LastLoudness = LastFloor = -1;
            LastOccluded = false;
            LastSkip = "none";
            _shownAt = -999f;
            _shownLoudness = -1;
            if (_live != null) Destroy(_live.gameObject);
            _live = null;
        }

        float _born;
        float _radius;
        bool _probe;
        LineRenderer _line;

        /// The colour of a ring at the instant it appears. Held here so the
        /// circle is the right colour the FIRST time it is rendered rather than
        /// on its first `Update` — which matters for the gate below, and would
        /// have been a one-frame white flash in the game regardless.
        static Color Fresh => new Color(0.85f, 0.88f, 0.95f, 0.55f);

        // ---------------------------------------------------------------
        // AND THE ONLY QUESTION THAT MATTERS: IS IT ON SCREEN
        // ---------------------------------------------------------------
        //
        // Everything above can be right and the player can still see nothing.
        // That is not a hypothetical — the ring's transform was rotated ninety
        // degrees about X while its vertices were ALREADY flat, which stood the
        // circle up like a hoop and pointed the ribbon at the ground. The
        // comment on that line said "flat on the ground rather than standing up
        // like a hoop" and the code did precisely the opposite, and no counter
        // in this file could have caught it.
        //
        // So the sim renders the same frame twice, once with this renderer off
        // and once with it on, and counts how many pixels got brighter. That is
        // the same A/B shape the occlusion and reflection gates use, for the
        // same reason: a thing that changes no pixels is not in the game.

        /// Build a ring the gate can render twice. It does not age, does not
        /// fade and does not destroy itself, because both renders must show the
        /// same circle — an animating probe would measure its own fade.
        public static NoiseRing ForVerification(Vector3 at, double radius)
        {
            var go = new GameObject("NoiseRingProbe");
            go.transform.position = at + Vector3.up * 0.04f;
            var ring = go.AddComponent<NoiseRing>();
            ring._radius = (float)radius;
            ring._born = Time.time;
            ring._probe = true;
            ring.Build();
            return ring;
        }

        public bool LineEnabled
        {
            get => _line != null && _line.enabled;
            set { if (_line != null) _line.enabled = value; }
        }

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

            // THE MEASUREMENT IS RECORDED FIRST, BEFORE EITHER REASON NOT TO
            // DRAW. Two cycles were lost to having it second.
            //
            // The claim being gated is "the radius the ring uses equals the
            // model's radius", and that is checkable for ANY radius. Whether it
            // clears the six-metre draw threshold is a presentation choice, and
            // whether a material exists is a build detail. Recording after
            // either of those made a legitimately quiet street — where nothing
            // is loud enough to be worth drawing — read as a broken hearing
            // model. Which is exactly backwards: a quiet street proving nothing
            // carries is the model working.
            LastRadius = r;
            LastLoudness = loudness;
            LastFloor = ambientFloorAtPlayer;
            LastOccluded = occluded;
            Sized++;
            if (r > MaxRadius) MaxRadius = r;

            // Each reason is named as it is taken, because "no ring appeared"
            // has three causes and only one of them is a fault.
            var verdict = Perception.RingDraw(r, loudness, _shownLoudness,
                                             Time.time - _shownAt);
            if (verdict == Perception.RingVerdict.TooSmall)
            { SkippedSmall++; LastSkip = "small"; return; }
            if (verdict == Perception.RingVerdict.Shadowed)
            { SkippedShadowed++; LastSkip = "shadowed"; return; }

            // A louder sound takes the ground from the one already there rather
            // than drawing over it — still one circle, now the right one.
            if (_live != null) Destroy(_live.gameObject);

            var go = new GameObject("NoiseRing");
            go.transform.position = at + Vector3.up * 0.04f;   // just off the road
            var ring = go.AddComponent<NoiseRing>();
            ring._radius = (float)r;
            ring._born = Time.time;
            ring.Build();

            // THE MATERIAL IS CHECKED AFTER THE FACT, not before, and that is a
            // correction. `Shader.Find` returning null does NOT mean there is
            // nothing to draw with: a `LineRenderer` created at runtime already
            // owns Unity's built-in line material, which ships with the
            // component and therefore cannot be stripped. Skipping the whole
            // ring because a named shader was missing threw away a perfectly
            // good circle — and, worse, it made "the shader got stripped" the
            // story I told about a bug that was really the cooldown.
            //
            // So: build it, then ask whether it actually has a material. That is
            // the real question, it is answerable, and it is answered here
            // rather than guessed at from a distance.
            if (ring._line == null || ring._line.sharedMaterial == null)
            {
                SkippedNoMaterial++;
                LastSkip = "no-material";
                Destroy(go);
                _live = null;
                return;
            }

            LastSkip = "drawn";
            Shown++;
            _shownAt = Time.time;
            _shownLoudness = loudness;
            _live = ring;
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

            // ONLY IF THERE IS SOMETHING BETTER. Assigning `Mat()` unconditionally
            // would overwrite the component's own built-in line material with
            // null when the named shader is absent, turning a survivable miss
            // into an invisible ring.
            var m = Mat();
            if (m != null) _line.material = m;

            // THE VERTICES GO IN THE LOCAL XY PLANE, NOT XZ, and that is the
            // whole of a bug that would have kept this invisible even after the
            // cooldown was fixed.
            //
            // `LineAlignment.TransformZ` means the ribbon's normal is the
            // transform's Z axis. For a circle lying on the road that normal
            // must point at the sky, so local +Z has to become world +Y — which
            // is a rotation of MINUS ninety about X, and it puts the ring's own
            // plane at local XY. The old code had the vertices flat in local XZ
            // (so their normal was local Y) and then rotated PLUS ninety, which
            // stood the circle upright in the world XY plane and aimed the
            // ribbon at the ground. Two mistakes that cancel into "nothing
            // visible", under a comment claiming the opposite.
            //
            // Worked through on paper because there is no way to look at it from
            // here: R(-90° about X) maps (x, y, z) to (x, z, -y), so local
            // (cos a, sin a, 0) becomes world (cos a, 0, -sin a) — flat on the
            // road — and local (0, 0, 1) becomes world (0, 1, 0) — facing up.
            for (int i = 0; i < Segments; i++)
            {
                float a = i / (float)Segments * Mathf.PI * 2f;
                _line.SetPosition(i, new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0) * _radius);
            }
            transform.rotation = Quaternion.Euler(-90, 0, 0);

            // Coloured HERE as well as in `Update`, so the first frame the ring
            // is rendered on is already the right colour rather than white.
            _line.startColor = Fresh;
            _line.endColor = Fresh;
        }

        void Update()
        {
            // A probe neither ages nor fades: both of the gate's renders have to
            // show the same circle, and a fading one would measure its own fade.
            if (_probe) return;

            float t = (Time.time - _born) / LifeSeconds;
            if (t >= 1f)
            {
                if (_live == this) _live = null;
                Destroy(gameObject);
                return;
            }

            // IT DOES NOT EXPAND. An expanding ring reads as a shockwave and
            // invites the player to watch it travel, which is a lie — the
            // radius is the answer, not the animation. It arrives at full size
            // and fades, so the size is the only thing carrying information.
            float alpha = 1f - t * t;
            var c = Fresh; c.a = alpha * Fresh.a;
            _line.startColor = c;
            _line.endColor = c;
        }
    }
}
