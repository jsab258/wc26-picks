using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The Unity end of `Core/Rig` (the-gap.md §3b).
    ///
    /// BUILT BEFORE THE CHARACTERS ARRIVE, and no longer waiting for them:
    /// `Mannequin` supplies a real joint hierarchy made of boxes, so the walk
    /// cycle, the limp, the look-split and the foot IK all run on a body
    /// today rather than on a capsule that leans.
    ///
    /// When a Mixamo FBX lands, importing it as **Humanoid** is the entire
    /// integration step — Unity's Avatar gives us HumanBodyBones, `Bind`
    /// prefers it, and nothing else here changes.
    ///
    /// Humanoid rather than bone-name matching on purpose. Mixamo's naming is
    /// stable ("mixamorig:LeftUpLeg") right up until somebody re-exports from
    /// Blender and it is not, and a rig that silently loses a leg because a
    /// prefix changed is a bad afternoon. The Avatar is the contract.
    ///
    /// Every number comes from Core. This class finds bones and applies
    /// rotations; it decides nothing.
    [DisallowMultipleComponent]
    public class CharacterRig : MonoBehaviour
    {
        Animator _animator;
        Transform _hips, _chest, _neck, _head;
        Transform _lFoot, _rFoot;
        Transform _lThigh, _lShin, _rThigh, _rShin;
        Transform _lUpperArm, _lForearm, _rUpperArm, _rForearm;
        Mannequin _mannequin;
        /// True once there is a skeleton to pose, from EITHER source.
        bool _posed;

        /// Real state, pushed in by whoever owns this body. Defaults are a
        /// healthy person standing still, so an unwired rig looks calm rather
        /// than dead.
        public double Stamina = 1.0;
        public double Capability = 1.0;
        public bool BadLegIsLeft = true;
        public double Speed;
        public double AccelMetresPerSecSq;
        public double TurnDegreesPerSec;
        /// What this body is looking at, or null for straight ahead.
        public Transform LookAt;

        /// Gait phase, 0..1, shared with the footstep audio so the limp you
        /// SEE and the limp you HEAR are the same limp.
        public double Phase;

        /// How far THIS person swings, relative to everyone else. A short
        /// brisk stride and a long loose one are recognisable across a street
        /// when height alone is not — and it is one multiply.
        public double GaitBias = 1.0;

        /// This body's own offset into the idle cycles, 0..1. Set from the
        /// physique so that a street of people standing about are not all
        /// shifting their weight on the same beat — which is far worse than
        /// all standing rigid, and is the thing that makes a crowd read as
        /// animated furniture.
        public double IdleOffset;

        float _breathTime;
        Quaternion _chest0, _neck0, _head0;
        Vector3 _hips0;
        bool _restCaptured;

        public static CharacterRig Attach(GameObject body)
        {
            if (body == null) return null;
            var rig = body.GetComponent<CharacterRig>();
            if (rig == null) rig = body.AddComponent<CharacterRig>();
            rig.Bind();
            return rig;
        }

        void Awake() { if (!_posed) Bind(); }

        /// THREE TIERS, most capable first: a bought Humanoid Avatar, the
        /// procedural `Mannequin`, and — if somehow neither — the capsule
        /// fallback that leans and breathes as one object.
        ///
        /// The tiers exist so the middle one can be DELETED without ceremony.
        /// When the FBX arrives, tier one starts matching, tier two stops
        /// being instantiated, and not one number below this method changes.
        void Bind()
        {
            _animator = GetComponentInChildren<Animator>();
            if (_animator != null && _animator.avatar != null && _animator.avatar.isHuman)
            {
                _posed = true;
                _hips = _animator.GetBoneTransform(HumanBodyBones.Hips);
                _chest = _animator.GetBoneTransform(HumanBodyBones.Chest)
                         ?? _animator.GetBoneTransform(HumanBodyBones.Spine);
                _neck = _animator.GetBoneTransform(HumanBodyBones.Neck);
                _head = _animator.GetBoneTransform(HumanBodyBones.Head);
                _lFoot = _animator.GetBoneTransform(HumanBodyBones.LeftFoot);
                _rFoot = _animator.GetBoneTransform(HumanBodyBones.RightFoot);
                _lThigh = _animator.GetBoneTransform(HumanBodyBones.LeftUpperLeg);
                _lShin = _animator.GetBoneTransform(HumanBodyBones.LeftLowerLeg);
                _rThigh = _animator.GetBoneTransform(HumanBodyBones.RightUpperLeg);
                _rShin = _animator.GetBoneTransform(HumanBodyBones.RightLowerLeg);
                _lUpperArm = _animator.GetBoneTransform(HumanBodyBones.LeftUpperArm);
                _lForearm = _animator.GetBoneTransform(HumanBodyBones.LeftLowerArm);
                _rUpperArm = _animator.GetBoneTransform(HumanBodyBones.RightUpperArm);
                _rForearm = _animator.GetBoneTransform(HumanBodyBones.RightLowerArm);
                CaptureRest();
                return;
            }

            var man = GetComponentInChildren<Mannequin>();
            if (man != null && man.Hips != null)
            {
                _posed = true;
                _animator = null;
                _hips = man.Hips; _chest = man.Chest; _neck = man.Neck; _head = man.Head;
                _lFoot = man.LFoot; _rFoot = man.RFoot;
                _lThigh = man.LThigh; _lShin = man.LShin;
                _rThigh = man.RThigh; _rShin = man.RShin;
                _lUpperArm = man.LUpperArm; _lForearm = man.LForearm;
                _rUpperArm = man.RUpperArm; _rForearm = man.RForearm;
                _mannequin = man;
                LegLength = Mannequin.ThighLength + Mannequin.ShinLength;
                // This person's own stride and their own bad leg. A crowd
                // where everybody limps on the left is a crowd with one
                // injury shared between them.
                GaitBias = man.Shape.Gait;
                BadLegIsLeft = man.Shape.BadLegIsLeft;
                IdleOffset = man.Shape.IdlePhase;
                CaptureRest();
                return;
            }

            // No skeleton at all. Everything that does not need one still
            // runs — which was the point of building this before the
            // characters existed, and is still the point if one fails to load.
            _posed = false;
        }

        void CaptureRest()
        {
            if (_chest != null) _chest0 = _chest.localRotation;
            if (_neck != null) _neck0 = _neck.localRotation;
            if (_head != null) _head0 = _head.localRotation;
            if (_hips != null) _hips0 = _hips.localPosition;
            _restCaptured = true;
        }

        void Update()
        {
            _breathTime += Time.deltaTime;
        }

        /// LateUpdate, always: the Animator writes the pose in Update, and
        /// anything additive applied before it is silently overwritten. This
        /// is the single most common way a procedural layer appears to do
        /// nothing at all.
        /// Beyond this, the rig stops solving. Not the body — the BODY stays,
        /// because the silhouette of a person is what makes a distant street
        /// read as populated and a stopped rig still holds its last pose.
        /// What stops is the maths: four limb solves, a look-split, IK
        /// raycasts and a breath, per person, per frame.
        ///
        /// Chosen to sit well outside the distance at which a stride is
        /// legible. If it is ever visible as a pop, it is too near — but the
        /// failure mode of getting it wrong is a distant figure gliding, and
        /// the failure mode of not having it is a frame budget spent on
        /// people nobody can see the legs of.
        public const float SolveWithinMetres = 34f;

        /// How many rigs solved on the last frame, for the perf gate. A
        /// distance cull that quietly stops culling is invisible until the
        /// frame time moves, and by then it is somebody else's bug.
        public static int SolvedLastFrame => _solvedShown;
        static int _solved, _solvedShown;
        static int _solvedFrame = -1;

        bool ShouldSolve()
        {
            var cam = Camera.main;
            if (cam == null) return true;
            // Squared, because this runs once per person per frame and a
            // square root here is the sort of thing that makes a culling
            // optimisation cost what it saves.
            float dx = transform.position.x - cam.transform.position.x;
            float dy = transform.position.y - cam.transform.position.y;
            float dz = transform.position.z - cam.transform.position.z;
            return dx * dx + dy * dy + dz * dz <= SolveWithinMetres * SolveWithinMetres;
        }

        void LateUpdate()
        {
            if (Time.frameCount != _solvedFrame)
            {
                _solvedFrame = Time.frameCount;
                _solvedShown = _solved;
                _solved = 0;
            }
            bool near = ShouldSolve();
            // The small pieces go with the solve. Same distance, one check,
            // and it keeps the two from disagreeing about what "far" means.
            if (_mannequin != null) _mannequin.SetDetail(near);
            if (!near) return;
            _solved++;

            var (pitch, roll) = Rig.Lean(AccelMetresPerSecSq, TurnDegreesPerSec, Speed);
            double breath = Rig.Breath(_breathTime, Stamina, Capability);
            var (stance, dip) = Rig.Limp(Capability, BadLegIsLeft, Phase);

            if (!_posed || !_restCaptured)
            {
                // CAPSULE MODE. The body leans and breathes as one object,
                // which is not a character but IS a proof that the numbers
                // reach the world — and it means the graybox already has
                // weight before a single model is bought.
                transform.localRotation = transform.localRotation
                    * Quaternion.Euler((float)pitch * 0.35f, 0, (float)roll * 0.35f);
                var p = transform.localPosition;
                p.y += (float)(breath * 0.35 + dip * 0.5);
                transform.localPosition = p;
                return;
            }

            // BACK TO REST FIRST, and only when there is no Animator.
            //
            // Every modulation below composes onto the current pose, which is
            // correct when an Animator has just rewritten that pose in Update
            // and catastrophic when nothing has. On a mannequin there is no
            // Animator, so the lean multiplied onto the chest each frame
            // compounds: a few degrees becomes a few hundred and the torso
            // spins. The bought characters would never have shown this, which
            // is exactly why it is worth writing down — the fallback path is
            // the one nobody re-reads.
            if (_animator == null && _restCaptured)
            {
                if (_chest != null) _chest.localRotation = _chest0;
                if (_neck != null) _neck.localRotation = _neck0;
                if (_head != null) _head.localRotation = _head0;
            }

            // ---- look-at: split down the spine, never the head alone ----
            if (LookAt != null && _head != null)
            {
                Vector3 to = LookAt.position - _head.position;
                Vector3 flat = Vector3.ProjectOnPlane(to, Vector3.up);
                if (flat.sqrMagnitude > 0.0001f)
                {
                    float yaw = Vector3.SignedAngle(transform.forward, flat, Vector3.up);
                    var (c, n, h) = Rig.LookSplit(yaw);
                    if (_chest != null)
                        _chest.localRotation = _chest0 * Quaternion.Euler(0, (float)c, 0);
                    if (_neck != null)
                        _neck.localRotation = _neck0 * Quaternion.Euler(0, (float)n, 0);
                    _head.localRotation = _head0 * Quaternion.Euler(0, (float)h, 0);
                    // The body comes round when the neck cannot get there.
                    // A decision, not a clamp.
                    MustTurn = Rig.MustTurnBody(yaw);
                }
            }
            else MustTurn = false;

            // ---- breathing and the limp, on the hips ----
            if (_hips != null)
            {
                var local = _hips0;
                local.y += (float)(breath + dip);
                // Both feet on their ground, so a kerb does not do the splits.
                local.y += (float)Rig.PelvisDrop(GroundUnder(_lFoot), GroundUnder(_rFoot), LegLength);
                _hips.localPosition = local;
            }

            // ---- the lean, on the chest ----
            if (_chest != null)
                _chest.localRotation = _chest.localRotation * Quaternion.Euler((float)pitch, 0, (float)roll);

            StanceScale = stance;

            DriveLimbs(stance);
        }

        /// THE WALK ITSELF, from `Core/Rig`. The limp's stance scale shortens
        /// the bad leg's swing rather than being applied separately, so the
        /// injury and the gait are one motion rather than two layered ones
        /// that fight over the same joint.
        ///
        /// SIGNS. A joint's mesh hangs down its local -Y, so a POSITIVE
        /// rotation about X swings that limb BACKWARD — every forward swing
        /// here is therefore negated. And knees and elbows are negated
        /// against each other on purpose: a knee flexes the shin backwards,
        /// an elbow flexes the forearm forwards. It looks like a sign bug in
        /// a diff and it is anatomy.
        void DriveLimbs(double stance)
        {
            // The bias scales the SPEED the cycle is asked about rather than
            // its output, so a loose-strided person also gets the knee lift
            // and the bob that go with a longer stride. Scaling the returned
            // angles would give them long legs and a short person's bounce.
            double gait = Speed * GaitBias;
            var lLeg = Rig.LegSwing(Phase, gait);
            var rLeg = Rig.LegSwing(Phase + 0.5, gait);
            // Same-side phase: the API already applied the opposition, so
            // the left arm takes the LEFT leg's phase.
            var lArm = Rig.ArmSwing(Phase, gait);
            var rArm = Rig.ArmSwing(Phase + 0.5, gait);

            double lScale = BadLegIsLeft ? stance : 1.0;
            double rScale = BadLegIsLeft ? 1.0 : stance;

            Swing(_lThigh, -lLeg.hip * lScale);
            Swing(_lShin, lLeg.knee * lScale);
            Swing(_rThigh, -rLeg.hip * rScale);
            Swing(_rShin, rLeg.knee * rScale);

            Swing(_lUpperArm, -lArm.shoulder);
            Swing(_lForearm, -lArm.elbow);
            Swing(_rUpperArm, -rArm.shoulder);
            Swing(_rForearm, -rArm.elbow);

            // Feet stay level with the ground rather than pointing wherever
            // the shin left them, which is the difference between walking and
            // marionetting.
            Level(_lFoot);
            Level(_rFoot);

            var (pelvisYaw, chestYaw) = Rig.Counterturn(Phase, gait);
            if (_hips != null)
                _hips.localRotation = Quaternion.Euler(0, (float)pelvisYaw, 0);
            if (_chest != null)
                _chest.localRotation = _chest.localRotation * Quaternion.Euler(0, (float)chestYaw, 0);

            // The bob rides on the hips with the breath and the limp dip.
            if (_hips != null)
            {
                var p = _hips.localPosition;
                p.y += (float)Rig.Bob(Phase, gait);
                _hips.localPosition = p;
            }

            Idle();
        }

        /// STANDING STILL, which is what most of a crowd is doing at any
        /// moment and was, until this, being done perfectly rigidly. A
        /// capsule reads as a placeholder; a motionless person reads as a
        /// corpse, and the difference cost the walk cycle nothing to create.
        ///
        /// Fades out as they start moving rather than switching off: a weight
        /// shift on top of a stride is two systems arguing over one hip.
        void Idle()
        {
            double amount = Rig.IdleAmount(Speed);
            if (amount <= 0.001 || _hips == null) return;

            double shift = Rig.WeightShift(_breathTime, IdleOffset);
            var (roll, lateral) = Rig.Stance(shift);
            double sway = Rig.Sway(_breathTime, IdleOffset * 0.7 + 0.31);

            _hips.localRotation = _hips.localRotation
                * Quaternion.Euler(0, 0, (float)(roll * amount));
            var p = _hips.localPosition;
            p.x += (float)(lateral * amount);
            p.z += (float)(sway * amount);
            _hips.localPosition = p;
        }

        static void Swing(Transform joint, double degrees)
        {
            if (joint != null) joint.localRotation = Quaternion.Euler((float)degrees, 0, 0);
        }

        /// Cancel a foot's inherited rotation so the sole stays parallel to
        /// the street. Cheap, and it fixes the single most obvious artefact of
        /// a swung-from-the-hip leg.
        void Level(Transform foot)
        {
            if (foot == null) return;
            foot.rotation = Quaternion.Euler(0, foot.rotation.eulerAngles.y, 0);
        }

        /// How far the last frame's limp shortened the bad leg's stance. Read
        /// by the footstep audio, so the sound and the pose come from one
        /// number rather than two that can drift apart.
        public double StanceScale { get; private set; } = 1.0;
        public bool MustTurn { get; private set; }

        public float LegLength = 0.88f;

        /// Ground height under a foot, or the foot's own height when there is
        /// nothing under it — which makes the IK a no-op rather than dragging
        /// the character into the floor.
        float GroundUnder(Transform foot)
        {
            if (foot == null) return 0f;
            var from = foot.position + Vector3.up * 0.5f;
            return Physics.Raycast(from, Vector3.down, out var hit, 1.5f,
                       ~0, QueryTriggerInteraction.Ignore)
                ? hit.point.y
                : foot.position.y;
        }
    }
}
