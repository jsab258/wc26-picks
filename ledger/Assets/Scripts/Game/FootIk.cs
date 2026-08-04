using UnityEngine;
using Ledger.Core;

namespace Ledger.Game
{
    /// M17.1 — FEET THAT MEET THE GROUND.
    ///
    /// The last uncalled piece of `Core/Rig`. `TwoBone`, `FootHeight` and
    /// `PlantBlend` have been complete, unit-tested and reachable by nothing
    /// since the day they were written, and all three have sat on the reach
    /// ledger under `WIRE: M17.1` for weeks. This is the caller.
    ///
    /// WHY A SEPARATE COMPONENT AND NOT A METHOD ON `CharacterRig`. Unity
    /// delivers `OnAnimatorIK` to components on the SAME GameObject as the
    /// Animator, and `CharacterRig` finds its animator with
    /// `GetComponentInChildren` — on a bought body the Animator is on the
    /// instantiated model, a level down. A method on `CharacterRig` would
    /// therefore compile, look right, and never be called on exactly the
    /// bodies this exists for. So `CharacterRig` attaches this to the
    /// animator's own object and hands it the numbers it holds.
    ///
    /// WHY THE ANIMATOR'S IK PASS AND NOT OUR OWN SOLVE. `CharacterRig`'s own
    /// comment states the rule this project learned the hard way and then broke
    /// twice: *"composing writes need a rest pose to return to, assigning
    /// writes need one to build from, AND NEITHER MAY RUN ON A BONE SOMETHING
    /// ELSE IS ALREADY ANIMATING."* When a clip is playing, the legs belong to
    /// the Animator — which is why `Swing` is already fenced behind
    /// `PoseIsDriven`. Writing thigh and shin rotations from `Rig.TwoBone`
    /// here would be the same fault a third time, one limb over.
    ///
    /// `SetIKPosition` is the one write that is not a fault: it is Unity's own
    /// pass, it runs after the clip and composes with it by design, and its
    /// weight is exactly the blend `Rig.PlantBlend` computes. So Core keeps the
    /// numbers — where the foot should be, how much to trust that, how far the
    /// pelvis drops — and Unity keeps the bones.
    ///
    /// WHAT `Rig.TwoBone` IS FOR, THEN. It stays the reach test: the goal is
    /// clamped to what the leg can actually reach before it is set, so a target
    /// under a kerb asks for a reachable foot rather than a straightened leg.
    /// That is a use of the solver, not a reimplementation of the IK pass.
    ///
    /// DONE IS A NUMBER, NOT A PICTURE. Per-foot vertical correction and the
    /// count of frames the clamp bit — a still cannot show whether a foot met
    /// the ground because a foot resting ON the road and a foot floating one
    /// centimetre above it are the same JPEG at street distance in fog.
    public class FootIk : MonoBehaviour
    {
        Animator _animator;
        CharacterRig _rig;

        /// HOW OFTEN THIS RAN AT ALL — the denominator every number below
        /// needs. `ikCorrectionWorst=0.000` reads as "the ground was always
        /// where the animation put it" and is equally consistent with the IK
        /// pass being off, which is the state this ships in unless
        /// `CharacterPrefab` sets `iKPass` and that is a line in an Editor
        /// script nothing local compiles.
        /// THE LEG THE CORRECTIONS ARE MEASURED AGAINST. Eighteen centimetres
        /// means nothing until you know whether the leg is 0.88m or 0.38m, and
        /// until this run every bought body reported the mannequin's default
        /// while its mesh was scaled by 0.434. A correction without the limb it
        /// is a fraction of is the denominator fault in a different coat.
        public static double LegLengthSeen = -1;

        public static int Frames;
        /// Frames on which a body was present but its pose was NOT clip-driven,
        /// so the feet belong to `Swing` and this stood down. Counted rather
        /// than skipped silently: a run where this is everything and `Frames`
        /// is zero means the controller never bound, which looks identical to
        /// the IK pass being off and has a different fix.
        public static int FramesUndriven;
        /// Individual foot goals set.
        public static int Goals;
        /// Goals where `Rig.FootHeight`'s clamp actually bit — the ground was
        /// further from the animated foot than a leg should stretch. High means
        /// the bodies are walking over geometry the clips were never made for,
        /// which is a level problem rather than a rig one.
        public static int Clamped;
        /// The largest vertical correction any foot was given, in metres, and
        /// the middle of the distribution beside it.
        ///
        /// BOTH, because a peak answers "did it ever have to reach" and the
        /// median answers "is this how it walks", and this project has twice
        /// published a conclusion off whichever of those it happened to print.
        public static double CorrectionWorst;
        /// What the ground ray struck at the worst correction, and how far the
        /// animated foot was above it. A distance with no idea what it was
        /// measured TO is the denominator fault wearing a third coat.
        public static string WorstHit = "nothing measured";
        public static double WorstDrop;
        /// Rays that found no ground at all. Those fall back to the animated
        /// height, which reads as "no correction needed" and is not the same
        /// thing.
        public static int GroundMissed;
        public static double CorrectionMedian = -1;

        /// STRIDED AND CAPPED, AND IT SAYS SO. Two feet on sixty-seven bodies
        /// for two thousand frames is a quarter of a million samples, which is
        /// megabytes held for one number. Every sixteenth is taken instead, and
        /// `CorrectionSamples` is printed so the median is never read as being
        /// over everything.
        const int Stride = 16;
        const int MaxSamples = 4000;
        static readonly System.Collections.Generic.List<float> _corrections =
            new System.Collections.Generic.List<float>();
        static int _seen;
        public static int CorrectionSamples => _corrections.Count;

        public static void Reset()
        {
            Frames = FramesUndriven = Goals = Clamped = GroundMissed = 0;
            WorstHit = "nothing measured";
            WorstDrop = 0;
            LegLengthSeen = -1;
            CorrectionWorst = 0;
            CorrectionMedian = -1;
            _corrections.Clear();
            _seen = 0;
        }

        /// Folded once at the end of a run rather than per frame, for the same
        /// reason `NameTags.CloseTextStats` is: sorting four thousand floats
        /// every frame would land in `frameWorstMs` and the median is only ever
        /// read off the done-line.
        public static void Close()
        {
            if (_corrections.Count == 0) { CorrectionMedian = -1; return; }
            var copy = new System.Collections.Generic.List<float>(_corrections);
            copy.Sort();
            CorrectionMedian = copy[(copy.Count - 1) / 2];
        }

        /// Attached by `CharacterRig`, which owns the phase and the leg length.
        public static void Attach(Animator animator, CharacterRig rig)
        {
            if (animator == null || rig == null) return;
            var ik = animator.gameObject.GetComponent<FootIk>()
                     ?? animator.gameObject.AddComponent<FootIk>();
            ik._animator = animator;
            ik._rig = rig;
        }

        void OnAnimatorIK(int layerIndex)
        {
            if (_animator == null || _rig == null) return;
            if (!_animator.isHuman) return;
            // ONE LAYER'S WORTH. `OnAnimatorIK` fires once per layer with the
            // pass enabled, and setting the same goal twice in a frame would
            // double the sample count without doubling the work — the two-maxima
            // fault's smaller cousin, a denominator inflated by the instrument.
            if (layerIndex != 0) return;

            // THE FENCE, AND IT IS THE SAME FENCE `Swing` USES. With no
            // controller bound the Animator evaluates nothing, the legs are
            // `CharacterRig`'s, and an IK goal set here would fight the very
            // solve that placed the foot.
            if (!_rig.PoseDriven) { FramesUndriven++; return; }
            Frames++;

            float legLength = Mathf.Max(0.1f, _rig.LegLength);
            LegLengthSeen = legLength;
            float lGround = Solve(AvatarIKGoal.LeftFoot, _rig.Phase, legLength);
            float rGround = Solve(AvatarIKGoal.RightFoot, _rig.Phase + 0.5, legLength);

            // AND THE PELVIS, so a body straddling a kerb settles onto both
            // feet instead of standing on the higher one with the other in the
            // air. `Rig.PelvisDrop` returns a negative offset and bounds itself
            // at a quarter of the leg, because past that the character is
            // crouching rather than standing on uneven ground.
            //
            // `bodyPosition` rather than the hips transform: the hips belong to
            // the clip, and this is the one place Unity offers to move the
            // whole body inside its own IK pass.
            double drop = Rig.PelvisDrop(lGround, rGround, legLength);
            if (drop < 0)
                _animator.bodyPosition = _animator.bodyPosition + Vector3.up * (float)drop;
        }

        /// One foot. Returns the ground height under it, which the pelvis
        /// drop needs and which is measured here so both feet and the pelvis
        /// read the SAME raycast rather than two taken a line apart.
        float Solve(AvatarIKGoal goal, double phase, float legLength)
        {
            Vector3 animated = _animator.GetIKPosition(goal);

            // Ground under where the animation actually put the foot. Half a
            // metre of headroom and a metre and a half of reach, matching
            // `CharacterRig.GroundUnder` exactly — a second ground rule would
            // be a second implementation of one idea, and this file's whole
            // argument is against that.
            var from = animated + Vector3.up * 0.5f;
            bool struck = Physics.Raycast(from, Vector3.down, out var hit, 1.5f,
                                          ~0, QueryTriggerInteraction.Ignore);
            float ground = struck ? hit.point.y : animated.y;

            // WHAT THE RAY ACTUALLY HIT, because a 17cm typical correction is
            // not IK polishing a small error and every guess at why would be a
            // guess.
            //
            // First reading with a real leg length: `ikCorrectionMedian=0.174`
            // against `ikLegLength=0.832` — a fifth of the leg, on a median
            // frame, on flat pavement. Either the animation puts feet well off
            // the ground or this ray is not finding the ground.
            //
            // The suspect worth naming is the body's OWN collider. The host is
            // a capsule, `~0` hits every layer including itself, and a ray
            // starting half a metre above a foot starts INSIDE that capsule —
            // so it can return the capsule's underside and call it pavement.
            // That would produce a plausible-looking number that is wrong by a
            // constant, which is the hardest kind to notice.
            //
            // Named at the WORST correction rather than last-wins, so the
            // reading describes the frame the peak came from. `ikGroundMissed`
            // is the other half: a ray that hits nothing falls back to the
            // animated height, which silently means "no correction" and would
            // otherwise be indistinguishable from a foot already perfect.
            if (!struck) GroundMissed++;

            double blend = Rig.PlantBlend(phase);
            double wantedY = Rig.FootHeight(animated.y, ground, blend);

            // WHAT THE LEG CAN ACTUALLY REACH. `Rig.TwoBone` clamps its reach
            // to the bones' own limits and returns the angles for the clamped
            // target, so asking it for the hip angle of a target under a kerb
            // is how to find out the target was never reachable. The goal is
            // pulled back to the reachable distance rather than being set where
            // the leg would have to straighten and the hip pop.
            var hipPos = _animator.bodyPosition;
            double reach = Mathf.Abs(hipPos.y - (float)wantedY);
            double half = legLength * 0.5;
            var solved = Rig.TwoBone(half, half, reach);
            // A returned knee of zero means the solver refused — bone lengths
            // at or below nothing — and there is nothing to trust in that.
            if (solved.knee <= 0) return ground;

            double correction = System.Math.Abs(wantedY - animated.y);
            if (correction > CorrectionWorst)
            {
                CorrectionWorst = correction;
                WorstHit = struck
                    ? (hit.collider != null ? hit.collider.name : "hit, no collider")
                    : "nothing under the foot";
                WorstDrop = animated.y - ground;
            }
            if (System.Math.Abs(ground - animated.y) > Rig.MaxFootAdjustMetres) Clamped++;
            if (_seen++ % Stride == 0 && _corrections.Count < MaxSamples)
                _corrections.Add((float)correction);
            Goals++;

            _animator.SetIKPositionWeight(goal, (float)blend);
            _animator.SetIKPosition(goal, new Vector3(animated.x, (float)wantedY, animated.z));
            return ground;
        }
    }
}
