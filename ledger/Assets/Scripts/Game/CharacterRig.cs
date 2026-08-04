using System.Collections.Generic;
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
    /// THE FBX HAVE LANDED, and "importing it as **Humanoid** is the entire
    /// integration step" — which is what this line said for weeks — was wrong
    /// by one caller. `Bind` did prefer the Avatar exactly as promised and
    /// nothing in this file needed changing; what broke was a caller elsewhere
    /// that had reached PAST this class for a bone, straight into `Mannequin`,
    /// and so could only ever see tier two. See `HandAnchor` below: the fix was
    /// to publish the joint from here, where both tiers are already resolved.
    /// Anything else that wants a named bone should ask this class for it
    /// rather than the body.
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
        /// The Avatar tier's real right hand bone. Null on the Mannequin tier,
        /// which ends the arm at the forearm and has no wrist joint.
        Transform _rHand;
        Transform _handAnchor;
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

        /// Whether this rig has offset its Animator's loop yet, and how many
        /// have across the run.
        ///
        /// COUNTED BECAUSE ZERO IS THE FAILURE AND IT IS SILENT. A phase seeded
        /// into a state machine that has not entered a state yet does nothing,
        /// and the symptom — twelve people stepping together — is exactly what
        /// the frame looked like BEFORE the fix. `phasesSeeded=0` beside a
        /// non-zero `walkerBodies` is that, said out loud, instead of a still
        /// somebody has to notice.
        bool _phaseSeeded;
        public static int PhasesSeeded { get; private set; }

        /// How far the hips assign moves a DRIVEN body from where its Animator
        /// put them, in metres, one sample per solved frame.
        ///
        /// Shared across rigs on purpose — the question is about the class of
        /// bodies, not about one walker, and twelve bought bodies at a time
        /// makes a per-rig median a sample of one person's gait.
        static readonly List<float> _hipOverrides = new List<float>();
        public static int HipOverrideSamples => _hipOverrides.Count;

        /// The median, or -1 when nothing driven was solved — which is a
        /// different finding from "the assign moves nothing" and must not read
        /// as one.
        public static double HipOverrideMedian
        {
            get
            {
                if (_hipOverrides.Count == 0) return -1;
                var c = new List<float>(_hipOverrides);
                c.Sort();
                return c[c.Count / 2];
            }
        }

        float _breathTime;
        Quaternion _chest0, _neck0, _head0;
        Vector3 _hips0;
        /// The hips' rest ROTATION, which was never captured — only the
        /// position was. That omission is the second half of the upside-down
        /// player: `Sway` multiplies onto `_hips.localRotation` every frame and
        /// there was no value to put it back to.
        Quaternion _hips0Rot = Quaternion.identity;
        /// Rest rotations for every limb `Swing` writes. See `Swing` — it
        /// ASSIGNS an absolute rotation, which is only correct when the rest
        /// pose is identity, and on a bought humanoid it never is.
        Quaternion _lThigh0 = Quaternion.identity, _lShin0 = Quaternion.identity;
        Quaternion _rThigh0 = Quaternion.identity, _rShin0 = Quaternion.identity;
        Quaternion _lUpperArm0 = Quaternion.identity, _lForearm0 = Quaternion.identity;
        Quaternion _rUpperArm0 = Quaternion.identity, _rForearm0 = Quaternion.identity;
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
        /// The tiers exist so the middle one can be DELETED without ceremony —
        /// and tier one now matches, on the player, since `RealBody` runs. Tier
        /// two is still what the crowd is made of and is not going anywhere
        /// until a skinned mesh has been costed on a GPU-less runner.
        ///
        /// So BOTH tiers are live at once, which the note here did not
        /// anticipate: it read as though the day tier one started matching was
        /// the day tier two stopped existing. Every consumer therefore has to
        /// work on either, and the way it does that is by reading the fields
        /// below rather than the body above.
        void Bind()
        {
            // THE REST POSE BELONGS TO A BODY, AND THE BODY CAN CHANGE UNDER
            // US. `_restCaptured` was set once and never cleared, which was
            // correct while a walker's body was chosen at spawn and kept for
            // ever. Body LOD swaps a mannequin for a skinned mesh at runtime,
            // and the stored rest rotations are then a previous skeleton's,
            // applied to transforms that have nothing to do with them — a body
            // that binds successfully and stands wrong, which is the failure
            // mode hardest to see in a still.
            _restCaptured = false;
            _posed = false;
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
                _rHand = _animator.GetBoneTransform(HumanBodyBones.RightHand);
                _handAnchor = null;
                CaptureRest();

                // THIS BODY'S OWN LEG, NOT THE MANNEQUIN'S.
                //
                // `LegLength` is assigned in the MANNEQUIN branch below and
                // nowhere else, so every bought body has been carrying the
                // default 0.88 — while `realBodyWhy` reports the mesh arriving
                // at 4.15m and being scaled by 0.434. The leg the code believed
                // in and the leg on screen were not the same object.
                //
                // TWO CALL SITES, ONE FAULT, and the older one is not mine:
                // `Rig.PelvisDrop` has bounded its drop at a quarter of this
                // number since bought bodies existed, and `FootIk` started
                // reading it an hour ago. The first reading from that build is
                // what exposed it — `ikCorrectionMedian=0.181`, a TYPICAL foot
                // being moved eighteen centimetres, which is not IK polishing a
                // small error but the animation and the ground disagreeing by a
                // large one.
                //
                // Measured from the bones in world space at bind time, so the
                // scale is already in it and no second scaling factor has to be
                // remembered anywhere. Falls back to the default rather than to
                // zero if a bone is missing, because a leg length of nothing
                // would make `PelvisDrop` clamp everything to zero and read as
                // the drop being disabled.
                float thighToShin = _lThigh != null && _lShin != null
                    ? Vector3.Distance(_lThigh.position, _lShin.position) : 0f;
                float shinToFoot = _lShin != null && _lFoot != null
                    ? Vector3.Distance(_lShin.position, _lFoot.position) : 0f;
                if (thighToShin > 0.01f && shinToFoot > 0.01f)
                    LegLength = thighToShin + shinToFoot;

                // FEET ON THE GROUND, and attached HERE rather than in
                // `LateUpdate` because Unity delivers `OnAnimatorIK` only to
                // components sharing a GameObject with the Animator — and on a
                // bought body that object is the instantiated model, a level
                // below this one. A method on this class would compile, read
                // correctly, and never be called on exactly the bodies foot IK
                // exists for.
                FootIk.Attach(_animator, this);
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
                _rHand = null;
                _handAnchor = null;
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

        /// Wrist to grip. A hand is about this deep and a held thing sits in the
        /// palm, not on the joint.
        const float HandPad = 0.05f;

        /// WHERE A HELD THING GOES, on whichever body this person turned out to
        /// have. The transform's ORIGIN is the grip and its local -Y runs out
        /// along the arm, so a caller parents at local zero and is done.
        ///
        /// THIS EXISTS BECAUSE THE TIER CHANGED UNDER A CALLER. `SimDirector`
        /// found the player's hand with `GetComponent&lt;Mannequin&gt;()`, which was
        /// the only body there was when it was written. `RealBody` then gave the
        /// player a bought skeleton instead — so the lookup returned null, the
        /// cosh was never drawn, and the threat gate went red reading
        /// `drawn=0 object=none`. Nothing was wrong with the threat; the hand had
        /// simply moved to a tier that caller could not see. `Bind` already
        /// resolves the arm for BOTH tiers, so the answer belongs here, once,
        /// where adding a fourth tier cannot break a caller again.
        ///
        /// Built lazily rather than in `Bind`, because most of a crowd never
        /// holds anything and this allocates a GameObject.
        public Transform HandAnchor
        {
            get
            {
                if (_handAnchor != null) return _handAnchor;
                _handAnchor = BuildHandAnchor();
                return _handAnchor;
            }
        }

        /// Which joint the last anchor was built on, for the verdict.
        ///
        /// ONE LINE, AND IT IS THE LINE THAT WOULD HAVE SAVED A BUILD. The
        /// threat gate failed reading `drawn=0 object=none`, which says the
        /// object was not drawn and says nothing about why — and the why was a
        /// body tier three files away. `verdict.txt` is the only channel out of
        /// CI this environment can read, so the tier goes in it.
        public static string HandTier { get; private set; } = "none";

        Transform BuildHandAnchor()
        {
            var parent = _rHand != null ? _rHand : _rForearm;
            if (parent == null) { HandTier = "no arm"; return null; }
            HandTier = _rHand != null ? "hand bone" : "forearm";

            var t = new GameObject("HandAnchor").transform;
            t.SetParent(parent, worldPositionStays: false);
            // The Avatar's hand bone IS the wrist. The Mannequin's forearm bone
            // is the ELBOW and the wrist is a forearm down it — and that length
            // is read from the builder rather than restated, because a second
            // copy of a dimension is a second thing to keep in step.
            t.localPosition = _rHand != null
                ? Vector3.zero
                : new Vector3(0f, -Mannequin.ForearmLength, 0f);
            t.localRotation = Quaternion.identity;

            // WHICH WAY IS DOWN THE ARM — MEASURED, NOT ASSUMED. On the
            // Mannequin the forearm's own -Y is the answer by construction. On a
            // bought rig the hand bone's local axes are whatever the exporter
            // chose, and this project's rule about Mixamo naming applies to
            // Mixamo AXES just as hard: a blade that comes out sideways because
            // a re-export rolled a bone is not a bug anybody would think to look
            // for. Elbow-to-wrist is a direction the skeleton cannot lie about.
            if (_rForearm != null)
            {
                Vector3 alongArm = t.position - _rForearm.position;
                if (alongArm.sqrMagnitude > 1e-6f)
                    t.rotation = Quaternion.FromToRotation(t.up, -alongArm.normalized) * t.rotation;
            }
            // And then out to the palm, along the axis just established. On the
            // Mannequin this lands at exactly the offset `HeldObject` used to
            // apply itself, so nothing that already worked moves.
            t.position -= t.up * HandPad;
            return t;
        }

        /// A cheap number that changes whenever this rig actually poses a bone.
        ///
        /// THE HOLE THIS CLOSES. The body gate reads
        /// `_bodyMaxKnee - _bodyMinKnee > 10` across EVERY rig, and that knee is
        /// computed from phase and speed rather than read off a transform — so
        /// fifty-five walking NPCs satisfy it while the player stands frozen in
        /// a T-pose, which given M17.1's week is the likeliest next fault and
        /// nothing was watching for it.
        ///
        /// Read off the transforms this class actually WRITES, so it answers
        /// "did the rig pose this body" rather than "would the maths have
        /// produced a pose". A body being pushed around by something else does
        /// not move it; a body nobody is posing leaves it bit-identical.
        ///
        /// Hips, chest and one knee: enough that a partial solve is visible, few
        /// enough that this is three quaternion reads at the end of a frame the
        /// rig was already solving.
        public float PoseSignature { get; private set; }

        /// IS THIS SHAPE A PERSON — asked of the BONES, not of the root.
        ///
        /// `RealBody.Upright` reads the root transform's up vector and it read
        /// 1.000 on a build whose player is a splayed red figure in the road
        /// with its limbs out. Both facts are true at once and neither is a
        /// bug in the other: the root IS upright, and the skeleton hanging off
        /// it is not a standing man. A gate on the root cannot see the pose,
        /// and I had written `bodyUp` believing it could.
        ///
        /// So: a head above its hips, and hips above its feet. Two signed
        /// metres, and the gate is on the SIGN rather than on a magnitude —
        /// which makes it not a threshold at all but a statement about which
        /// way a person is assembled. The magnitudes are printed so a real
        /// bound (a head is ~0.55m above the hips, hips ~0.9m above the sole)
        /// can be set from evidence on the next run instead of guessed now.
        ///
        /// WORLD SPACE, and deliberately: local positions are relative to a
        /// parent that may itself be the thing that is wrong, which is exactly
        /// how the Z-up import hid for a build.
        public float HeadAboveHips { get; private set; }
        public float HipsAboveFeet { get; private set; }
        public bool PostureRead { get; private set; }

        /// The same two measurements taken BEFORE this class touches a bone —
        /// the Animator's own output. See the note at the top of `LateUpdate`:
        /// the pair is a bisect, and reading them together is what makes it one
        /// CI round trip instead of two.
        public float PreHeadAboveHips { get; private set; }
        public float PreHipsAboveFeet { get; private set; }
        public bool PrePoseRead { get; private set; }

        /// WHAT THE AVATAR ITSELF THINKS UP IS, which is the one quantity in
        /// this whole investigation nobody has read.
        ///
        /// The bracket has narrowed the fault to the retarget: bind pose
        /// upright, scaled pose upright, the Animator's output inverted. That
        /// leaves exactly three possibilities and every one of them has a
        /// different fix, so guessing between them is how the last two
        /// proposed fixes came to be wrong.
        ///
        ///   the avatar's mapping is inverted   -> `BodyPitch`/`BodyRoll` near 180
        ///   the CLIP's curves are inverted     -> body upright, bones inverted
        ///   there is no clip and the rest pose
        ///   is what we are looking at          -> `ClipName` empty
        ///
        /// `bodyRotation` is the avatar's own notion of the body's orientation
        /// in muscle space, computed by the retarget rather than read off our
        /// bones — so it can disagree with the skeleton, and the disagreement
        /// IS the diagnosis. Pure reads, no side effects: this probe cannot
        /// itself become the thing that moves the body, which a `Rebind` test
        /// could.
        public float BodyPitch { get; private set; }
        public float BodyRoll { get; private set; }
        public string ClipName { get; private set; } = "";
        public bool AvatarProbeRead { get; private set; }

        void StampAvatar()
        {
            if (_animator == null || !_animator.isHuman) return;
            // Euler angles are read as a signed swing about each axis so an
            // inversion reads as ~180 rather than as 359-and-a-bit, which is
            // the same number wearing a disguise.
            var e = _animator.bodyRotation.eulerAngles;
            BodyPitch = Mathf.DeltaAngle(0f, e.x);
            BodyRoll = Mathf.DeltaAngle(0f, e.z);
            if (_animator.runtimeAnimatorController != null && _animator.layerCount > 0)
            {
                var infos = _animator.GetCurrentAnimatorClipInfo(0);
                ClipName = infos.Length > 0 && infos[0].clip != null ? infos[0].clip.name : "";
            }
            else ClipName = "";
            AvatarProbeRead = true;
        }

        /// Shared by both samples so the two cannot drift apart. A bisect whose
        /// halves measure slightly different things proves nothing.
        bool ReadPosture(out float headAboveHips, out float hipsAboveFeet)
        {
            headAboveHips = hipsAboveFeet = 0f;
            if (_hips == null || _head == null || (_lFoot == null && _rFoot == null))
                return false;
            float soleY = _lFoot != null && _rFoot != null
                ? Mathf.Min(_lFoot.position.y, _rFoot.position.y)
                : (_lFoot != null ? _lFoot.position.y : _rFoot.position.y);
            headAboveHips = _head.position.y - _hips.position.y;
            hipsAboveFeet = _hips.position.y - soleY;
            return true;
        }

        void StampPrePose()
        {
            if (ReadPosture(out float h, out float f))
            {
                // THE FIRST FRAME, KEPT SEPARATELY, BECAUSE THE BRACKET HAS A
                // HOLE IN IT AND THIS IS THE THIRD TIME.
                //
                // `PreHeadAboveHips` is sampled at the TOP of `LateUpdate`,
                // which is after the PREVIOUS frame's solve — bones persist
                // between frames. So "pre-solve" and "post-solve" both see
                // accumulated state, and the pair can never distinguish "the
                // Animator handed us an inverted pose" from "we inverted it on
                // an earlier frame and nothing put it back". I read that pair
                // as indicting the retarget. It cannot indict anything.
                //
                // The twin says the same thing from the other side: an Animator
                // bound to this avatar with no controller reads +0.557/+0.955,
                // exactly upright, while the player reads -0.115. The twin's
                // only other difference is that its `CharacterRig` was
                // destroyed.
                //
                // On the FIRST frame this component ever runs, nothing has
                // solved. If that reading is upright and later ones are not,
                // the pose is being accumulated rather than delivered, and the
                // comment forty lines below — "the bought characters would
                // never have shown this" — is false: `clip=[]` says the bought
                // body has an Animator and NOTHING PLAYING, so nothing rewrites
                // the pose each frame and the compounding that guard was
                // written for applies to it exactly as it does to a mannequin.
                if (!FirstPreRead)
                {
                    FirstPreHeadAboveHips = h;
                    FirstPreHipsAboveFeet = f;
                    FirstPreRead = true;
                }
                PreHeadAboveHips = h;
                PreHipsAboveFeet = f;
                PrePoseRead = true;
            }
        }

        /// The pre-solve posture on the very first frame this rig ran, before
        /// any solve of ours could have touched it. Static because there is one
        /// player and the question is about that body, and because a per-
        /// instance value would be overwritten by sixty-eight mannequins.
        public static float FirstPreHeadAboveHips { get; private set; }
        public static float FirstPreHipsAboveFeet { get; private set; }
        public static bool FirstPreRead { get; private set; }

        /// Angle between the upper arm and straight down in the REST pose:
        /// 0 is arms at the sides, 90 is a T-pose. Static because the question
        /// is about the one bought body, and sixty-eight mannequins would
        /// overwrite a per-instance value.
        public static float RestArmDropDegrees { get; private set; }
        public static bool RestArmRead { get; private set; }

        /// Whether this rig's Animator has anything to play at all. If it does
        /// not, the Animator cannot be rewriting the pose each frame, and every
        /// modulation below composes onto its own output for ever.
        public bool HasController =>
            _animator != null && _animator.runtimeAnimatorController != null;

        /// Whether anything OTHER THAN THIS CLASS writes these bones each frame.
        ///
        /// The distinction the rest-restore needed and did not have. An Animator
        /// that exists but has no controller evaluates nothing, so the pose it
        /// "produces" is simply whatever was there last frame — which, when this
        /// class is the only writer, is this class's own previous output.
        /// Composing onto that is composing onto yourself, for ever.
        bool PoseIsDriven => _animator != null
                             && _animator.runtimeAnimatorController != null
                             && _animator.enabled;

        /// The same question, asked from outside. `FootIk` has to stand down on
        /// exactly the bodies `Swing` stands UP on, and two copies of that test
        /// would drift apart the first time either changed — which is the fault
        /// this file's own comments record happening to the ground raycast and
        /// to the billboard aim.
        public bool PoseDriven => PoseIsDriven;

        /// The same angle as `RestArmDropDegrees`, measured AFTER the solve.
        ///
        /// The rest reading came back 0.0 — arms hanging straight down — and
        /// the still shows them straight out sideways. Both cannot be true of
        /// the same frame, so one number is measuring something other than what
        /// I think it is, and that is exactly the position the torso was in
        /// before the four-stage bracket settled it.
        ///
        /// This is the other end of the bracket. Rest 0 and live 90 means
        /// something between them lifts the arms and it can be found by
        /// elimination. Rest 0 and live 0 means the BONES are down while the
        /// mesh renders out, which is a skinning problem and nothing to do with
        /// the rig at all — a completely different search, and worth knowing
        /// before spending a night on the wrong one.
        /// WHETHER THIS RIG IS THE ONE BODY ANYBODY IS ASKING ABOUT.
        ///
        /// Every arm reading was a MAXIMUM over all sixty-eight rigs, so
        /// `liveArmDrop=122.4` named no body: it could have been the player's
        /// bought skeleton or any mannequin in the crowd, and the three numbers
        /// in the bracket were not guaranteed to describe the SAME PERSON.
        /// `restArmDrop=7.8` alongside `preArmDrop=108.1` is exactly that —
        /// one figure with its arms down and a different one with them out,
        /// reported as though they were a before and an after.
        ///
        /// A bracket whose arms measure different subjects proves nothing,
        /// which is rule 3 pointed at my own instrument. Only the driven body
        /// reports now; the crowd is measured by `bodiesOk` and its own knee
        /// range, which is what those exist for.
        bool IsTheBoughtBody => _animator != null && _mannequin == null;

        void StampArmsPre()
        {
            if (!IsTheBoughtBody) return;
            float a = ArmDropNow();
            if (a < 0f) return;
            if (a > PreArmDropDegrees) PreArmDropDegrees = a;
            PreArmRead = true;
        }

        /// The blend-tree float. Must match `CharacterPrefab.SpeedParam`, and
        /// is spelled out here rather than referenced because that type is
        /// Editor-only and this one ships.
        public const string SpeedParam = "Speed";

        /// Whether anything ever wrote that float. A controller that exists
        /// and is never driven looks identical, from a screenshot, to no
        /// controller at all — so the run says which.
        public static bool SpeedDriven { get; private set; }

        /// The bought body's animator, reported rather than assumed. A
        /// controller that exists and never evaluates looks identical from
        /// every number the run had until now.
        public static string AnimCulling = "not read";
        public static float AnimClipTime;
        public static int AnimStateHash;

        /// How far an arm sits from vertical when it is simply hanging. Not a
        /// measurement and not claimed as one — it is the small outward angle a
        /// person's arms make against their own body, and it exists so the
        /// hands do not intersect the coat.
        public const float ArmSplayDegrees = 8f;

        /// Rotate one arm from wherever it is to a natural hang.
        ///
        /// `sign` splays it away from the body: positive for the left arm,
        /// negative for the right, so both go outward rather than both going
        /// the same way — which would put one arm through the ribs and is the
        /// obvious way to get this wrong.
        void HangArm(Transform upper, Transform fore, float sign)
        {
            if (upper == null) return;
            var arm = fore != null ? (fore.position - upper.position) : -upper.up;
            if (arm.sqrMagnitude <= 1e-6f) return;
            // Down, tilted outward around the body's own forward axis. Built
            // from `transform`, not from world axes, so it stays right for a
            // body standing on a slope or facing any direction.
            var want = Quaternion.AngleAxis(sign, transform.forward) * -transform.up;
            upper.rotation = Quaternion.FromToRotation(arm.normalized, want.normalized)
                             * upper.rotation;
        }

        /// Angle of the left upper arm from straight down, or -1 if unreadable.
        /// ONE reader for all three samples — rest, pre-solve, post-solve — so
        /// the arms of a bracket cannot drift apart. That is the `ReadPosture`
        /// lesson: three numbers only bracket a fault if one function made them.
        float ArmDropNow()
        {
            if (_lUpperArm == null) return -1f;
            var down = -transform.up;
            var arm = _lForearm != null
                ? (_lForearm.position - _lUpperArm.position)
                : -_lUpperArm.up;
            if (arm.sqrMagnitude <= 1e-6f) return -1f;
            return Vector3.Angle(arm.normalized, down);
        }

        /// Widest the arms got BEFORE this class touched them, over the run.
        public static float PreArmDropDegrees { get; private set; }
        public static bool PreArmRead { get; private set; }

        void StampArmsNow()
        {
            if (!IsTheBoughtBody) return;
            float a = ArmDropNow();
            if (a < 0f) return;
            if (a > LiveArmDropDegrees) LiveArmDropDegrees = a;
            LiveArmRead = true;
        }

        /// Widest the arms got over the run, in degrees from straight down.
        /// Worst-over-run because the question is "do they EVER stick out",
        /// and a sample taken mid-stride answers a different one.
        public static float LiveArmDropDegrees { get; private set; }
        public static bool LiveArmRead { get; private set; }

        void StampPose()
        {
            StampArmsNow();
            float s = 0f;
            if (_hips != null) s += _hips.localPosition.y * 977f + _hips.localRotation.x;
            if (_chest != null) s += _chest.localRotation.x * 31f + _chest.localRotation.z;
            if (_rShin != null) s += _rShin.localRotation.x * 7f;
            PoseSignature = s;

            if (ReadPosture(out float h, out float f))
            {
                HeadAboveHips = h;
                HipsAboveFeet = f;
                PostureRead = true;
            }
        }

        void CaptureRest()
        {
            if (_chest != null) _chest0 = _chest.localRotation;
            if (_neck != null) _neck0 = _neck.localRotation;
            if (_head != null) _head0 = _head.localRotation;
            if (_hips != null) { _hips0 = _hips.localPosition; _hips0Rot = _hips.localRotation; }
            if (_lThigh != null) _lThigh0 = _lThigh.localRotation;
            if (_lShin != null) _lShin0 = _lShin.localRotation;
            if (_rThigh != null) _rThigh0 = _rThigh.localRotation;
            if (_rShin != null) _rShin0 = _rShin.localRotation;
            // BRING THE ARMS DOWN FIRST, WHEN NOTHING ELSE WILL.
            //
            // A bought Humanoid ships in a T-pose and `X Bot` is no exception:
            // the bracket read `preArmDrop=118.6` before a single line of this
            // class runs and `liveArmDrop=118.6` after, the same number to a
            // tenth of a degree. Our solve is innocent — it composes a swing of
            // at most 22 degrees onto whatever rest it was given, and the rest
            // it was given is a man holding his arms out.
            //
            // The real fix is a controller with a breathing idle, which
            // `CharacterPrefab` now builds. This is the OTHER half: if that
            // build fails — a wrong Editor API, a missing clip — the body still
            // stands like a person instead of a scarecrow, and the frame shows
            // one fault rather than two. `PoseIsDriven` is the switch: with
            // something actually animating these bones, the Animator owns them
            // and this must not touch them.
            //
            // MEASURED, NOT GUESSED. It does not test the angle against a
            // threshold and it does not assume a T-pose — it computes the
            // rotation that takes the arm WHEREVER IT IS onto a natural hang,
            // so it is correct for a T-pose, an A-pose and a body already
            // right (where it is the identity). The only authored number is
            // the splay, and eight degrees is an arm resting against a coat
            // rather than clipping through one.
            if (!PoseIsDriven)
            {
                HangArm(_lUpperArm, _lForearm, +ArmSplayDegrees);
                HangArm(_rUpperArm, _rForearm, -ArmSplayDegrees);
            }

            if (_lUpperArm != null) _lUpperArm0 = _lUpperArm.localRotation;
            if (_lForearm != null) _lForearm0 = _lForearm.localRotation;
            if (_rUpperArm != null) _rUpperArm0 = _rUpperArm.localRotation;
            if (_rForearm != null) _rForearm0 = _rForearm.localRotation;

            // HOW FAR THE ARMS HANG IN THE REST POSE, which is the last thing
            // visibly wrong with the player and is a hypothesis until this
            // reads.
            //
            // The still shows him standing correctly with his arms straight
            // out sideways. `Swing` now composes from rest, and at a standstill
            // the arm swing is near zero — so what is on screen IS the rest
            // pose. A bought Humanoid ships in a T-pose; `Mannequin` builds its
            // arms hanging down, which is exactly why sixty-eight procedural
            // bodies look fine and the one purchased body does not.
            //
            // Measured as the angle between the upper arm and straight down, so
            // 0 is arms at the sides and 90 is a T-pose. If it reads near 90 the
            // fix is a rest pose with the arms lowered — sampled from one of the
            // forty-four imported clips rather than invented — and if it reads
            // near 0 then something else is holding them out and the obvious
            // fix would have been wrong.
            // THROUGH THE SHARED READER, like the other two samples. This block
            // used to carry its own copy of the same six lines, which is the
            // drift `ReadPosture` was rewritten to stop: three numbers compared
            // against each other in a bracket are only comparable if one
            // function produced all three. The `_hips != null` guard it also
            // carried was decorative — no term in the angle uses the hips.
            float rest = ArmDropNow();
            if (rest >= 0f && IsTheBoughtBody)
            {
                RestArmDropDegrees = rest;
                RestArmRead = true;
            }
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

        /// The same distance, from the graphics preset. `SolveWithinMetres`
        /// stays as the High value it always was, so a default install
        /// behaves exactly as it did before presets existed.
        public static float DetailWithinMetres =>
            (float)Ledger.Core.Detail.BodyDetailDistance(
                Ledger.Core.Detail.Parse(GameSettings.Current.Detail));

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
            float r = DetailWithinMetres;
            return dx * dx + dy * dy + dz * dz <= r * r;
        }

        void LateUpdate()
        {
            using (Perf.Time("rigs")) LateUpdateBody();
        }

        /// WHAT A CHARACTER COSTS, which is the third measurement the cast
        /// tiering was owed and the only one nobody had taken.
        ///
        /// `Recurrence` says what the DESIGN wants — 6.5 distinct faces a day
        /// at seven districts, 12.9 at three — and `Density` says what the
        /// witness engine needs, about twenty near an event. Neither says what
        /// the machine allows, so the cast size has been bounded from one side
        /// only and a proposal was about to be made on that.
        ///
        /// HONEST ABOUT WHAT THIS RUNNER CAN ANSWER. It has no GPU and
        /// software-rasterises everything, so a millisecond of skinning
        /// measured here is a number about a software rasteriser and transfers
        /// nowhere. What DOES transfer is the CPU-side cost of the game's own
        /// per-character code, which is this scope, and the geometric load —
        /// bones, vertices, instances — which is what any GPU estimate needs as
        /// its input. Measuring the transferable half and saying so is worth
        /// more than a millisecond figure that would be quoted for a year and
        /// be wrong on every real machine.
        void LateUpdateBody()
        {
            if (Time.frameCount != _solvedFrame)
            {
                _solvedFrame = Time.frameCount;
                _solvedShown = _solved;
                _solved = 0;
            }
            // THE BISECT, TAKEN HERE RATHER THAN IN A SEPARATE BUILD.
            //
            // The player renders upside down while the BIND pose measures
            // correct (`RealBody.BindHeadAboveHips` 0.557, `BindHipsAboveFeet`
            // 0.955), so the import is innocent and something after it inverts
            // the body. Two suspects with opposite fixes: the animation clip or
            // the avatar binding, versus this rig's own solve.
            //
            // The obvious experiment is a build with the solve disabled, then
            // another with it back. That is two round trips at ~28 minutes each
            // and a revert to remember. Sampling HERE — after the Animator has
            // written the clip's pose, before a single line of this class
            // touches a bone — gets both numbers out of ONE run and needs no
            // revert. If the pre-solve pose is upright and the post-solve pose
            // is not, the fault is in this file. If both are inverted, the
            // Animator handed us an inverted pose and the fault is the clip or
            // the avatar.
            StampPrePose();
            // THE MISSING MIDDLE OF THE ARM BRACKET. Rest reads 0 degrees —
            // arms straight down — and after the solve they read 118.8, which
            // is past horizontal. `ArmSwing` cannot do that: it returns (0,0)
            // at a standstill and maxes at 22 degrees anywhere.
            //
            // So the same bisect that settled the torso, and the same reason it
            // worked: this samples BEFORE any line of this class touches a
            // bone, so it splits the two candidates cleanly. Already 118.8 here
            // means the Animator's own default pose is doing it and our solve
            // is innocent; 0 here and 118.8 after means the solve does it and
            // `Swing` composing onto a rest rotation is not the harmless thing
            // it looks like.
            StampArmsPre();
            // AND TELL THE CONTROLLER HOW FAST THIS BODY IS MOVING.
            //
            // Without this the blend tree sits at zero for ever and a walking
            // man plays a breathing idle while sliding down the street — which
            // is the classic version of "the animation system is wired and
            // nothing drives it", and would have looked like the controller
            // failing to build rather than a float nobody wrote.
            //
            // `Speed` is the same metres-per-second the procedural gait
            // already runs on, so the clip and the footfalls agree by
            // construction instead of by tuning.
            if (PoseIsDriven)
            {
                _animator.SetFloat(SpeedParam, (float)Speed);
                if (!SpeedDriven) { SpeedDriven = true; }

                // AND THE PERSON'S OWN CADENCE AND PHASE, WHICH THIS BRANCH
                // IGNORED WHILE THE PROCEDURAL ONE HONOURED BOTH.
                //
                // Found by grepping `Breadth` after fixing the bought bodies'
                // uniform scale, then grepping the rest of `Physique` for the
                // same shape — which is rule 1's third corollary paying out
                // three times in one sweep. `GaitBias` appears exactly once in
                // this file outside its declaration, in `DriveLimbs`, and
                // `IdleOffset` twice, in the procedural breath and sway.
                // Neither reaches the Animator. So `NpcWalker` sets all three
                // traits on every walker — with a comment explaining that it
                // sets them unconditionally so the two tiers "cannot disagree
                // about who walks how" — and on the twelve nearest people, the
                // ones actually wearing bought bodies, all three were written
                // and dropped.
                //
                // `speed` RATHER THAN THE BLEND PARAMETER. Scaling the float
                // the tree blends on would make a loose-strided person appear
                // to be MOVING faster and pick a run clip while walking; the
                // playback rate changes the cadence at the same ground speed,
                // which is what a gait bias means. Same argument `DriveLimbs`
                // makes one screen down for why it scales the speed the cycle
                // is asked about rather than the angles it returns.
                //
                // THE PHASE IS SEEDED ONCE, not driven. Every bought body
                // starts its controller at normalised time zero, so twelve
                // people in shot breathe and step in lockstep — the one way
                // real bodies could read as worse than thirteen boxes, which
                // the roadmap says was deliberately avoided for the mannequins
                // and was then reintroduced here by omission. Writing it every
                // frame would fight the state machine; writing it at the first
                // driven frame offsets the whole loop for ever after.
                if (_animator.speed != (float)GaitBias)
                    _animator.speed = (float)GaitBias;
                if (!_phaseSeeded)
                {
                    _phaseSeeded = true;
                    var seed = _animator.GetCurrentAnimatorStateInfo(0);
                    _animator.Play(seed.shortNameHash, 0, (float)IdleOffset);
                    PhasesSeeded++;
                }
                // WHAT THE ANIMATOR IS ACTUALLY DOING, because "it has a
                // controller" and "it is animating" turned out to be different
                // facts and only the first was measured. `speedDriven=True`
                // said the float was written; it said nothing about whether
                // anything read it.
                if (IsTheBoughtBody)
                {
                    AnimCulling = _animator.cullingMode.ToString();
                    var st = _animator.GetCurrentAnimatorStateInfo(0);
                    // Normalised time ADVANCES when a clip is playing and sits
                    // still when it is not. One number, and it separates "no
                    // controller", "controller with no motion" and "playing".
                    if (st.normalizedTime > AnimClipTime) AnimClipTime = st.normalizedTime;
                    AnimStateHash = st.shortNameHash;
                }
            }
            // Beside the pre-solve sample, because they answer the same question
            // from opposite ends: `PreHeadAboveHips` is what the BONES say after
            // the retarget, `BodyPitch` is what the AVATAR says it did. One run,
            // both readings, and the pair partitions every remaining case.
            StampAvatar();

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
            // THE CONDITION WAS "IS THERE AN ANIMATOR" AND HAD TO BE "IS
            // ANYTHING REWRITING THE POSE". That gap is the upside-down player,
            // and it took five round trips to find because every reading I took
            // was of a body that had already been wrong for hundreds of frames.
            //
            // The comment above says the compounding "is correct when an
            // Animator has just rewritten that pose in Update and catastrophic
            // when nothing has", and then ends "the bought characters would
            // never have shown this." They showed it. The bought body HAS an
            // Animator — `playerHasController=False`, `clip=[]`, so it has one
            // with nothing in it. It therefore failed the `_animator == null`
            // test, never got restored to rest, and every frame's lean and
            // breath and limp multiplied onto the previous frame's output until
            // the man was upside down in mid-air.
            //
            // Measured, not reasoned: `firstPreHeadAboveHips=0.659` — UPRIGHT on
            // the first frame this component ever ran, before any solve of ours
            // — against -0.135 later in the same run. Nothing else touches those
            // bones. The no-clip twin, identical but with its `CharacterRig`
            // destroyed, stayed at +0.557 all run.
            //
            // An Animator with no controller drives nothing. Ask what it DOES,
            // not whether it EXISTS.
            if (!PoseIsDriven && _restCaptured)
            {
                if (_chest != null) _chest.localRotation = _chest0;
                if (_neck != null) _neck.localRotation = _neck0;
                if (_head != null) _head.localRotation = _head0;
                // AND THE HIPS, WHICH THE FIRST VERSION OF THIS LEFT OUT.
                //
                // Restoring three bones took `headAboveHips` from -0.136 to
                // +0.520 — the torso came the right way up — and left
                // `hipsAboveFeet` at -0.775, because `Sway` does
                // `_hips.localRotation = _hips.localRotation * ...` and the
                // lateral shift does `p.x +=`, both of which compound exactly
                // like the chest did. `CaptureRest` saved the hips POSITION and
                // nothing ever read it back, and it never saved the rotation at
                // all.
                //
                // A restore list is a claim that it names every bone the solve
                // composes onto, and that claim is invisible in a diff. The
                // legs are safe because `Swing` ASSIGNS rather than multiplies —
                // which is the distinction worth carrying: composing writes need
                // a rest pose, assigning writes do not.
                if (_hips != null)
                {
                    _hips.localRotation = _hips0Rot;
                    _hips.localPosition = _hips0;
                }
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

                // HOW FAR THIS ASSIGN MOVES A DRIVEN BODY'S HIPS FROM WHERE THE
                // ANIMATOR PUT THEM — a reading, and deliberately only that.
                //
                // This line ASSIGNS from the rest position. Six screens down
                // the pelvis ROTATION is composed on a driven body instead,
                // under a comment giving the reason: "An assign here would
                // flatten the clip's own pelvis rotation and undo half of any
                // walk cycle." The same argument is true of POSITION and
                // nobody applied it here, so a bought body's vertical rhythm is
                // the clip's, discarded, and replaced by `Rig.Bob(Phase)` — a
                // second bob driven by a phase the clip does not share.
                //
                // WHETHER THAT MATTERS IS A NUMBER I DO NOT HAVE. If the clip
                // barely moves its hips the assign is harmless; if it carries
                // the whole bob, this is throwing away the animation and is a
                // candidate for the foot behaviour `FootIk` has been chasing
                // all day. Changing it blind, in the file where an inverted
                // assumption cost two builds this morning, is how that morning
                // happened. So: measure, read, then decide (rule 2).
                //
                // MEDIAN OVER THE RUN, not a peak: the question is "is the
                // clip's hip motion being discarded", which is about the
                // typical frame, and a maximum would be whichever frame the
                // pelvis drop caught somebody on a kerb.
                if (PoseIsDriven && _hipOverrides.Count < 20000)
                    _hipOverrides.Add(Mathf.Abs(_hips.localPosition.y - local.y));

                _hips.localPosition = local;
            }

            // ---- the lean, on the chest ----
            if (_chest != null)
                _chest.localRotation = _chest.localRotation * Quaternion.Euler((float)pitch, 0, (float)roll);

            StanceScale = stance;

            DriveLimbs(stance);

            // LAST, after everything that writes a bone. Stamped here rather
            // than anywhere earlier so it reflects the pose that was actually
            // left on the transforms — the same reasoning as `DriveBody` going
            // last in `NpcWalker`, where a gait measured before the walk
            // disagrees with where the body went.
            StampPose();
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

            // SWUNG FROM REST, NOT TO AN ABSOLUTE, and that is the rest of the
            // upside-down player.
            //
            // `Swing` assigned `Quaternion.Euler(degrees, 0, 0)` outright,
            // which is correct only when a bone's rest rotation is identity.
            // `Mannequin` builds its joints that way, so this was right for
            // every body the game had until one was bought — and a Humanoid
            // FBX carries real rest orientations on every limb, so assigning
            // over them threw the model's own skeleton away and replaced it
            // with a pitch about nothing.
            //
            // It is NOT the compounding fault fixed above, and the numbers say
            // so plainly: `hipsAboveFeet` sat at -0.777 and stayed there.
            // Accumulation grows; this was constant, which is the signature of
            // a wrong absolute rather than a runaway. Both were live at once,
            // which is why the first fix moved the torso and left the legs.
            // THE LIMBS BELONG TO WHOEVER IS DRIVING THE POSE, AND ONLY ONE
            // THING CAN OWN A BONE.
            //
            // `Swing` ASSIGNS `rest * Euler(degrees, 0, 0)`, where `rest` was
            // captured once. That is correct on a mannequin, which has no other
            // writer. On a body with an Animator it overwrites the clip every
            // frame with a stale snapshot — so the first build with a real
            // locomotion controller came back `speedDriven=True
            // controller=ok(idle+walk+run)` and a figure standing with one arm
            // bent up beside its head, which is no clip and no rest pose but a
            // blend of both.
            //
            // This is the third face of the same lesson and it is worth stating
            // once more: composing writes need a rest pose to return to,
            // assigning writes need one to build from, AND NEITHER MAY RUN ON A
            // BONE SOMETHING ELSE IS ALREADY ANIMATING. `PoseIsDriven` already
            // guarded the rest-restore and the arm hang; it did not guard the
            // thing that actually writes the limbs.
            //
            // What stays when a clip is playing: the lean, the breath and the
            // chest counterturn, because those COMPOSE onto whatever the
            // Animator just wrote and are the expressive layer the clips cannot
            // know about — how tired this person is, how hurt, which way they
            // are banking. That was always the design; it simply had no case
            // where a clip existed.
            if (!PoseIsDriven)
            {
                Swing(_lThigh, _lThigh0, -lLeg.hip * lScale);
                Swing(_lShin, _lShin0, lLeg.knee * lScale);
                Swing(_rThigh, _rThigh0, -rLeg.hip * rScale);
                Swing(_rShin, _rShin0, rLeg.knee * rScale);

                Swing(_lUpperArm, _lUpperArm0, -lArm.shoulder);
                Swing(_lForearm, _lForearm0, -lArm.elbow);
                Swing(_rUpperArm, _rUpperArm0, -rArm.shoulder);
                Swing(_rForearm, _rForearm0, -rArm.elbow);

                // Feet stay level with the ground rather than pointing wherever
                // the shin left them, which is the difference between walking
                // and marionetting. Nothing to level when a clip placed them.
                Level(_lFoot);
                Level(_rFoot);
            }

            var (pelvisYaw, chestYaw) = Rig.Counterturn(Phase, gait);
            // ASSIGNED on a mannequin, COMPOSED on a driven body — the same
            // distinction, one line lower. An assign here would flatten the
            // clip's own pelvis rotation and undo half of any walk cycle.
            if (_hips != null)
                _hips.localRotation = PoseIsDriven
                    ? _hips.localRotation * Quaternion.Euler(0, (float)pelvisYaw, 0)
                    : Quaternion.Euler(0, (float)pelvisYaw, 0);
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

        /// Rotate a joint `degrees` about its own X from ITS REST POSE.
        ///
        /// The rest quaternion is not optional and not a default. Omitting it
        /// is assigning an absolute, which silently works on any skeleton whose
        /// bind rotations are identity and silently destroys any skeleton whose
        /// are not — and the difference does not show up until somebody buys a
        /// character. Taking it as a parameter means a new caller has to supply
        /// one rather than inherit the bug.
        static void Swing(Transform joint, Quaternion rest, double degrees)
        {
            if (joint != null)
                joint.localRotation = rest * Quaternion.Euler((float)degrees, 0, 0);
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
