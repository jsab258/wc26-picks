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

        /// WHAT THE COMPONENT'S OWN MATERIAL ACTUALLY IS. One string, and it
        /// answers the question I would otherwise ask a build for next: whether
        /// the built-in line material alpha-blends. If it does not, the ring
        /// renders opaque and the fade in `Update` does nothing, and it will pop
        /// off the screen rather than fade — visible, and wrong in a way no
        /// counter would report. Spaces stripped because this goes into a
        /// key=value verdict line.
        public static string PaintUsed = "unknown";

        /// WHICH MATERIAL DRAWS THE LINE — and this is an enum because guessing
        /// cost four builds and measuring cost one.
        ///
        /// WHAT THE LAST RUN ACTUALLY ESTABLISHED, all of it measured:
        ///   * `ringNoMaterial=4` — a `LineRenderer` created at runtime has NO
        ///     material in this build. `sharedMaterial` is null. The comment
        ///     below used to claim the component "already owns Unity's built-in
        ///     line material, which ships with the component and therefore
        ///     cannot be stripped", and that was confident and false.
        ///   * `sprites=0.7279` against `default=0.7279`, identical to four
        ///     decimals — assigning `Sprites/Default` changed nothing, because
        ///     `Shader.Find` returned null for it. It is not in the build.
        ///   * `particles=0.0000` — `Legacy Shaders/Particles/Alpha Blended` IS
        ///     in the build and drew nothing measurable.
        ///   * `control=17.8073` — the A/B itself sees fine, so none of the
        ///     above is a measurement artefact.
        ///
        /// Hence `Ledger`: this project's own shader, in `Assets/Resources`,
        /// which is the reason the grade and the light shafts work where a
        /// built-in name does not. The rest are kept only so the sweep can keep
        /// reporting them — a fact that took four builds to establish should not
        /// be re-establishable by accident.
        public enum Paint
        {
            /// WHAT THE GAME USES: `Hidden/LedgerRing`, unlit, vertex-coloured,
            /// alpha blended, and present in the player because everything in
            /// `Assets/Resources` is.
            Ledger,
            /// Assign nothing and see what a null material does. Measured
            /// 0.7279% of the frame, which means Unity draws SOMETHING — almost
            /// certainly the magenta error shader. Visible is not the same as
            /// correct and this is not shippable.
            None,
            SpritesDefault,
            ParticlesAlphaBlended,
        }

        static Material _ledger;

        /// Null means "leave whatever the component came with", which is now
        /// known to be nothing at all.
        static Material Made(Paint paint)
        {
            switch (paint)
            {
                case Paint.Ledger:
                {
                    if (_ledger != null) return _ledger;
                    var ls = Shader.Find("Hidden/LedgerRing");
                    // Cached and shared: one ring exists at a time, so one
                    // material is all this ever needs, and the fade rides on
                    // the LineRenderer's vertex colours rather than on the
                    // material — which is what makes sharing safe.
                    if (ls != null) _ledger = new Material(ls)
                        { hideFlags = HideFlags.HideAndDontSave };
                    return _ledger;
                }
                case Paint.SpritesDefault:
                {
                    var s = Shader.Find("Sprites/Default");
                    return s != null ? new Material(s) : null;
                }
                case Paint.ParticlesAlphaBlended:
                {
                    var s = Shader.Find("Legacy Shaders/Particles/Alpha Blended")
                            ?? Shader.Find("Particles/Alpha Blended");
                    return s != null ? new Material(s) : null;
                }
                default:
                    return null;
            }
        }

        /// HOW THE CIRCLE IS LAID OUT — and this is an enum for the same reason
        /// `Paint` is. My geometry fix rests on reading `LineAlignment.TransformZ`
        /// as "the ribbon's normal is the transform's Z axis". If that reading is
        /// backwards then the fix made things worse, and I cannot look at the
        /// screen to find out.
        ///
        /// So the shipping layout does not depend on that reading at all — and
        /// just as well, because the reading was wrong: `FlatTransformZ` measured
        /// zero changed pixels and `FlatBillboard` measured 0.7279%.
        public enum Lay
        {
            /// SHIPPING. Vertices flat in local XZ — which is the ground plane in
            /// world space with no rotation whatsoever — and the ribbon
            /// billboarded to the camera, which cannot be edge-on by
            /// construction. Two unambiguous choices instead of two that have to
            /// cancel correctly.
            FlatBillboard,
            /// Vertices in local XY with a -90 rotation about X and the ribbon
            /// aligned to the transform's Z. MEASURED AT 0.0000% AND THEREFORE
            /// WRONG — my reading of the alignment doc did not survive contact
            /// with a rendered frame. Kept because a wrong answer that has been
            /// paid for is worth keeping next to the right one.
            FlatTransformZ,
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

        /// WOULD A SOUND THIS LOUD BE SHADOWED IF IT HAPPENED RIGHT NOW?
        ///
        /// Asked by the sim before it STAGES a sound, because rule 5b's twin
        /// says a guard needs a run in which the thing it asserts can happen.
        /// `perception` has been red on `ring-drawn` with four slams staged and
        /// not one ring among them: the sim was spending its four chances inside
        /// other sounds' shadows and then failing itself for the absence.
        ///
        /// The radius argument is a SENTINEL, and it has to be. `RingDraw` asks
        /// two questions in sequence — is it big enough, then is it shadowed —
        /// and only the second one is being asked here. Passing one metre over
        /// the minimum walks past the first branch without pretending to know
        /// the real radius, which depends on an ambient floor this class is not
        /// holding. A caller wanting the size question has `Show` and its
        /// `LastRadius`.
        public static bool WouldBeShadowed(double loudness) =>
            Perception.RingDraw(Perception.RingMinRadiusMetres + 1, loudness,
                                _shownLoudness, Time.time - _shownAt)
                == Perception.RingVerdict.Shadowed;

        /// HIDE THE TEACHING OVERLAY WHILE A REVIEW STILL IS TAKEN.
        ///
        /// `review_day1_night.jpg` is a white arc sweeping the entire frame,
        /// edge to edge, over a street you can barely see behind it. That is
        /// this class working exactly as designed: `ringMax=148.1` metres, and
        /// a 148-metre circle seen from inside is a straight band, half a metre
        /// thick, across the world.
        ///
        /// The four stills exist to answer ONE question — what does the street
        /// look like — and they were answering "what does the street look like
        /// with a debug overlay on it". Nothing is weakened by hiding it: the
        /// ring's own evidence is an A/B render (`ringSeen` against
        /// `ringNone`), taken in its own frames with its own camera pass, and
        /// it does not read these files.
        ///
        /// THIS IS NOT THE WHOLE FIX AND MUST NOT BE MISTAKEN FOR IT. A player
        /// would see that band too. A ring only reads AS a ring while its
        /// curvature is visible: the sagitta of a chord `L` on radius `R` is
        /// about `L²/8R`, so a thirty-metre span of a 148-metre ring bows by
        /// 0.76m and is a straight line to the eye. Past roughly forty metres
        /// the shape stops carrying its meaning and becomes a stripe. Fading it
        /// out over that range is a real change to game feel and wants its own
        /// commit and its own frame, not a rider on a screenshot fix.
        public static bool HiddenForCapture;

        /// Show or hide the live ring around a capture. Returns whether one was
        /// actually there, so a still taken on a silent street cannot be read
        /// as proof that the hiding worked.
        public static bool SetHiddenForCapture(bool hidden)
        {
            HiddenForCapture = hidden;
            if (_live == null) return false;
            var lr = _live.GetComponent<LineRenderer>();
            if (lr != null) lr.enabled = !hidden;
            return true;
        }

        /// Zeroed with the rest of the perception counters at the start of a
        /// sim run, so the numbers in the verdict describe THIS run.
        public static void Reset()
        {
            Sized = Shown = SkippedSmall = SkippedShadowed = SkippedNoMaterial = 0;
            MaxRadius = -1;
            LastRadius = LastLoudness = LastFloor = -1;
            LastOccluded = false;
            LastSkip = "none";
            PaintUsed = "unknown";
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
        public static NoiseRing ForVerification(Vector3 at, double radius,
                                                Paint paint, Lay lay)
        {
            var go = new GameObject("NoiseRingProbe");
            go.transform.position = at + Vector3.up * 0.04f;
            var ring = go.AddComponent<NoiseRing>();
            ring._radius = (float)radius;
            ring._born = Time.time;
            ring._probe = true;
            ring.Build(paint, lay);
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
            ring.Build(Paint.Ledger, Lay.FlatBillboard);

            // THE MATERIAL IS CHECKED AFTER THE FACT, and it is a real check
            // rather than a formality. The previous version of this comment said
            // a runtime LineRenderer "already owns Unity's built-in line
            // material, which ships with the component and therefore cannot be
            // stripped". CI answered that with `ringNoMaterial=4`: it is null,
            // every time, and four rings were thrown away for it.
            //
            // Which is exactly why the check is here and why it is counted
            // separately. A ring skipped for having nothing to draw with looks
            // identical to a quiet street unless something says which it was.
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

        void Build(Paint paint, Lay lay)
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

            // ONLY IF THERE IS SOMETHING TO PUT THERE. For the shipping path
            // this is null and the component keeps its own built-in material.
            var m = Made(paint);
            if (m != null) _line.material = m;

            // THE OLD CODE HAD TWO MISTAKES THAT CANCELLED INTO NOTHING
            // VISIBLE: vertices flat in local XZ (normal = local Y) and then a
            // rotation of PLUS ninety about X, which stands the circle upright
            // in the world XY plane and aims the ribbon at the road — under a
            // comment reading "flat on the ground rather than standing up like a
            // hoop".
            //
            // Both replacements below are laid out so that NOTHING has to
            // cancel. `FlatBillboard` puts the vertices in local XZ, which is the
            // ground plane with no rotation at all, and lets the ribbon face the
            // camera, which cannot be edge-on. `FlatTransformZ` is the version
            // that depends on my reading of the alignment doc, kept only so the
            // sim can tell me whether that reading was right.
            //
            // Worked on paper because there is no way to look at it from here:
            // R(-90 about X) maps (x, y, z) to (x, z, -y), so local
            // (cos a, sin a, 0) becomes world (cos a, 0, -sin a) — flat on the
            // road — and local (0, 0, 1) becomes world (0, 1, 0) — facing up.
            bool billboard = lay == Lay.FlatBillboard;
            _line.alignment = billboard ? LineAlignment.View : LineAlignment.TransformZ;
            for (int i = 0; i < Segments; i++)
            {
                float a = i / (float)Segments * Mathf.PI * 2f;
                _line.SetPosition(i, billboard
                    ? new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * _radius
                    : new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0) * _radius);
            }
            transform.rotation = billboard
                ? Quaternion.identity : Quaternion.Euler(-90, 0, 0);

            if (!_probe && _line.sharedMaterial != null && _line.sharedMaterial.shader != null)
                PaintUsed = _line.sharedMaterial.shader.name.Replace(' ', '_');

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
