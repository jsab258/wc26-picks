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
        /// Goals where the blend said the foot was planted, and the middle of
        /// their corrections. A planted foot ought to be on the ground; a
        /// swinging one ought not, and mixing them is what makes the overall
        /// median unable to accuse anything.
        public static int PlantedGoals;
        public static double PlantedMedian = -1;
        static readonly System.Collections.Generic.List<float> _planted =
            new System.Collections.Generic.List<float>();
        public static double CorrectionMedian = -1;

        /// HOW FAR THE ANIMATED FOOT IS ABOVE THE ROAD, before the IK touches
        /// it — over every goal, and over the planted ones alone.
        ///
        /// THESE EXIST BECAUSE THE FORK ABOVE COULD NOT ANSWER ITS OWN
        /// QUESTION, and the comment that set it up is fifty lines below this
        /// one. It said: if the planted median is small the body is fine, and
        /// if it is "as large as the overall one" the IK is being applied at
        /// the wrong moments. The second half is unreachable.
        ///
        /// `correction` is `|wantedY - animated.y|` and `wantedY` comes from
        /// `Rig.FootHeight(animated.y, ground, blend)`, which returns
        /// `animated.y` when the blend is zero. So a swinging foot contributes
        /// a STRUCTURAL zero — not a small number, an arithmetic one — and
        /// roughly half of every walk cycle is swinging. The overall median is
        /// the planted median diluted by those zeros and can only ever be
        /// SMALLER. `ikCorrectionMedian=0.031` against `ikPlantedMedian=0.073`
        /// is that dilution and nothing else; the two were one measurement
        /// twice, which is the shape this project keeps writing into comments
        /// and believing.
        ///
        /// The drop is the quantity the blend does not touch. If `PlantBlend`
        /// is timed to the clip, planted frames are the frames the foot is
        /// DOWN, and `PlantedDropMedian` should be far below `DropMedian`. If
        /// the two clocks are independent, "planted" is a random slice of the
        /// cycle and the two medians land on top of each other. That test
        /// cannot be satisfied by construction, which is the whole difference.
        ///
        /// SIGNED, deliberately. A foot under the road and a foot above it are
        /// different faults — one is a clip walking through geometry, the other
        /// is a rig floating — and `System.Math.Abs` would print them as the
        /// same number.
        public static double DropMedian = -1;
        public static double PlantedDropMedian = -1;
        static readonly System.Collections.Generic.List<float> _drops =
            new System.Collections.Generic.List<float>();
        static readonly System.Collections.Generic.List<float> _plantedDrops =
            new System.Collections.Generic.List<float>();
        public static int DropSamples => _drops.Count;
        /// Frames where the procedural gait phase said "planted" and the feet
        /// disagreed. The size of the fault the change above fixes, reported
        /// rather than asserted — and a zero here would mean the two clocks
        /// happened to agree and the change bought nothing.
        public static int PlantDisagreed;
        public static int PlantedDropSamples => _plantedDrops.Count;

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
            _planted.Clear();
            PlantedGoals = 0;
            PlantedMedian = -1;
            _drops.Clear();
            PlantDisagreed = 0;
            _plantedDrops.Clear();
            DropMedian = -1;
            PlantedDropMedian = -1;
            _seen = 0;
        }

        /// Folded once at the end of a run rather than per frame, for the same
        /// reason `NameTags.CloseTextStats` is: sorting four thousand floats
        /// every frame would land in `frameWorstMs` and the median is only ever
        /// read off the done-line.
        public static void Close()
        {
            CorrectionMedian = Middle(_corrections);
            PlantedMedian = Middle(_planted);
            DropMedian = Middle(_drops);
            PlantedDropMedian = Middle(_plantedDrops);
        }

        /// ONE MEDIAN, FOUR CALLERS. The first version inlined it twice and the
        /// second copy carried an early `return` that skipped the planted one
        /// whenever the corrections list was empty — a guard on one list
        /// silently deciding another list's answer. Four copies of that would
        /// have been four chances at it.
        ///
        /// -1 FOR EMPTY, WHICH IS NOT SAFE ON ITS OWN FOR THE DROPS. A drop of
        /// 0.000 is a foot exactly on the road — the best possible reading — so
        /// zero cannot mean "nothing sampled"; but the drop series is SIGNED,
        /// and a foot a metre under the road would print -1 too. The counts
        /// below are the denominator that separates them, and they are printed
        /// for exactly that reason.
        static double Middle(System.Collections.Generic.List<float> xs)
        {
            if (xs.Count == 0) return -1;
            var copy = new System.Collections.Generic.List<float>(xs);
            copy.Sort();
            return copy[(copy.Count - 1) / 2];
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

            // WHICH FOOT IS DOWN — ASKED OF THE FEET, NOT OF A PHASE.
            //
            // MEASURED TWICE BEFORE BEING CHANGED. `ikPlantedDropMedian` and
            // `ikDropMedian` came back 0.059 against 0.055, then 0.043 against
            // 0.042: the frames the blend calls PLANTED are indistinguishable
            // from every other frame. If the plant were timed to the clip they
            // would be far apart, because a planted foot is a foot that is
            // down. They are not, so it is not.
            //
            // The cause was named before either reading, so it cannot be
            // fitted afterwards: `Rig.PlantBlend` is driven by
            // `CharacterRig.Phase`, the PROCEDURAL gait phase, while the foot
            // itself comes from a bought Mixamo clip with its own timing. Two
            // independent clocks for one idea — the shape that has already cost
            // this project the arms, the billboards and the ground raycast
            // twice each.
            //
            // THE LOWER FOOT IS THE PLANTED ONE, and that needs no constant at
            // all — no window height, no threshold to measure, nothing to get
            // wrong. It is also true of every gait rather than of a walk: in a
            // run, a limp or a stand, the foot nearer the ground is the one
            // taking the weight. Compared BEFORE either is corrected, because
            // the correction is what would erase the difference.
            float lY = _animator.GetIKPosition(AvatarIKGoal.LeftFoot).y;
            float rY = _animator.GetIKPosition(AvatarIKGoal.RightFoot).y;
            // A DEAD BAND, because two feet at exactly the same height is a
            // stand rather than a step, and in a stand BOTH are planted. A
            // strict comparison would pick one at random and let the other
            // float, which is the sort of thing that reads as a limp.
            const float BothDown = 0.02f;
            bool lPlanted = lY <= rY + BothDown;
            bool rPlanted = rY <= lY + BothDown;

            float lGround = Solve(AvatarIKGoal.LeftFoot, _rig.Phase, legLength, lPlanted);
            float rGround = Solve(AvatarIKGoal.RightFoot, _rig.Phase + 0.5, legLength, rPlanted);

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
        float Solve(AvatarIKGoal goal, double phase, float legLength, bool planted)
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

            // THE BLEND COMES FROM WHICH FOOT IS DOWN NOW.
            //
            // `Rig.PlantBlend(phase)` is still what shapes it — a hard 0 or 1
            // would snap the foot onto the ground at the instant of contact and
            // off it again, which is the visible fault this whole pass exists
            // to avoid — but it is asked about a phase that MEANS something to
            // this foot rather than about the procedural gait clock. A planted
            // foot is asked at the middle of its stance and a swinging one at
            // the middle of its swing, so the curve still eases and the timing
            // now belongs to the clip.
            //
            // `PlantedFromPhase` keeps the count of frames where the old
            // procedural answer and the new one disagreed, which is the number
            // that says how wrong it was rather than asserting it.
            //
            // I HAD THESE BACKWARDS AND THE RUN SAID SO WITHIN THE HOUR. The
            // first version asked for 0.25 when planted and 0.75 when
            // swinging, on an assumption about what a phase means that I never
            // checked against the function. `Rig.PlantBlend` says it plainly:
            // "Down through 0.15..0.35, planted 0.35..0.75, up through
            // 0.75..0.9." So 0.25 is mid-DESCENT and comes out at 0.5, and
            // 0.75 is the last instant of the plant and comes out at 1.0 —
            // exactly inverted. The IK was pulling the SWINGING foot onto the
            // ground at full weight, which is the one thing the blend exists
            // to prevent.
            //
            // The measurement caught it and could not have been clearer: the
            // feet being called planted read 0.177 above the road against an
            // overall 0.050, anti-correlated rather than merely uninformative,
            // and the planted share fell from about half of all goals to 14%.
            // Both are the signature of picking the wrong foot.
            //
            // 0.55 is the middle of the planted band and 0.0 is outside every
            // band, so the two answers are now the extremes the curve was
            // written to produce rather than two points I guessed at.
            double clipPhase = planted ? 0.55 : 0.0;
            if ((Rig.PlantBlend(phase) > 0.9) != planted) PlantDisagreed++;
            double blend = Rig.PlantBlend(clipPhase);
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

            // ONE STRIDE DECISION FOR ALL FOUR SERIES, TAKEN BEFORE THE
            // COUNTER MOVES. The first version wrote `_seen++ % Stride` here
            // and `_seen % Stride` twenty lines down, so the planted samples
            // came from a stride offset by one from the corrections — two
            // series that read as the same sample set and were not. Harmless
            // to a median and not harmless to anybody comparing them frame by
            // frame later, which is the only reason to print them together.
            bool sample = _seen % Stride == 0;
            _seen++;
            double drop = animated.y - ground;
            if (sample && _corrections.Count < MaxSamples)
                _corrections.Add((float)correction);
            if (sample && _drops.Count < MaxSamples) _drops.Add((float)drop);

            // AND THE SAME NUMBER FOR A FOOT THAT IS SUPPOSED TO BE PLANTED,
            // which is the one that can accuse the blend rather than the body.
            //
            // The ray is innocent: `ikWorstHit=[Road_10]` and
            // `ikGroundMissed=0`, so it finds the road every time and my prime
            // suspect — the body's own capsule — was wrong. What is left is
            // that the animated foot really is up to half a metre above the
            // road (`ikWorstDrop=0.498`) and typically a fifth of one.
            //
            // A SWINGING foot SHOULD be off the ground, and `PlantBlend`
            // correctly asks for no correction there, so those samples belong
            // in the median and drag it nowhere. A PLANTED foot should be ON
            // it. So the planted-only median is the discriminating number: if
            // it is small, the body is fine and the overall median is just the
            // walk cycle; if it is as large as the overall one, the IK is being
            // applied at the wrong moments.
            //
            // THE SUSPECT THIS TESTS. `Rig.PlantBlend` is driven by
            // `CharacterRig.Phase` — the PROCEDURAL gait phase — while the foot
            // position comes from a Mixamo CLIP with its own timing. Those two
            // are independent, so "planted" can land anywhere in the clip's
            // cycle. That would be one idea with two clocks, which is this
            // project's most repeated shape.
            //
            // THE FORK ABOVE IS RIGGED AND `ikPlantedMedian=0.073` AGAINST
            // `ikCorrectionMedian=0.031` DID NOT TEST IT. `correction` is
            // computed FROM `blend`: at blend zero `Rig.FootHeight` returns the
            // animated height unchanged, so every swinging goal contributes an
            // arithmetic zero. The overall median is the planted one diluted by
            // those zeros and is therefore always the smaller of the two,
            // whatever the rig is doing. Two numbers out of one variable, read
            // as agreement — the fault this project keeps writing into its own
            // comments, three sites now.
            //
            // `drop` is what the blend cannot touch. Planted frames should be
            // the frames the foot is DOWN, so `ikPlantedDropMedian` well below
            // `ikDropMedian` means the blend is timed to the clip, and the two
            // landing together means it is not. Both outcomes are reachable,
            // which is the only property the first test lacked.
            if (blend > 0.9)
            {
                PlantedGoals++;
                if (sample && _planted.Count < MaxSamples)
                    _planted.Add((float)correction);
                if (sample && _plantedDrops.Count < MaxSamples)
                    _plantedDrops.Add((float)drop);
            }
            Goals++;

            _animator.SetIKPositionWeight(goal, (float)blend);
            _animator.SetIKPosition(goal, new Vector3(animated.x, (float)wantedY, animated.z));
            return ground;
        }
    }
}
