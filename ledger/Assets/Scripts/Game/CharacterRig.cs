using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The Unity end of `Core/Rig` (the-gap.md §3b).
    ///
    /// BUILT BEFORE THE CHARACTERS ARRIVE, and it runs on capsules today: if
    /// there is no skeleton it drives the transform it is on, which is enough
    /// to prove the lean, the breathing and the limp against the graybox.
    /// When a Mixamo FBX lands, importing it as **Humanoid** is the entire
    /// integration step — Unity's Avatar gives us HumanBodyBones and nothing
    /// here changes.
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
        bool _humanoid;

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

        void Awake() { if (!_humanoid) Bind(); }

        void Bind()
        {
            _animator = GetComponentInChildren<Animator>();
            if (_animator == null || _animator.avatar == null || !_animator.avatar.isHuman)
            {
                // No skeleton yet. Everything that does not need one still
                // runs — which is the point of building this now.
                _humanoid = false;
                return;
            }
            _humanoid = true;
            _hips = _animator.GetBoneTransform(HumanBodyBones.Hips);
            _chest = _animator.GetBoneTransform(HumanBodyBones.Chest)
                     ?? _animator.GetBoneTransform(HumanBodyBones.Spine);
            _neck = _animator.GetBoneTransform(HumanBodyBones.Neck);
            _head = _animator.GetBoneTransform(HumanBodyBones.Head);
            _lFoot = _animator.GetBoneTransform(HumanBodyBones.LeftFoot);
            _rFoot = _animator.GetBoneTransform(HumanBodyBones.RightFoot);
            CaptureRest();
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
        void LateUpdate()
        {
            var (pitch, roll) = Rig.Lean(AccelMetresPerSecSq, TurnDegreesPerSec, Speed);
            double breath = Rig.Breath(_breathTime, Stamina, Capability);
            var (stance, dip) = Rig.Limp(Capability, BadLegIsLeft, Phase);

            if (!_humanoid || !_restCaptured)
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
