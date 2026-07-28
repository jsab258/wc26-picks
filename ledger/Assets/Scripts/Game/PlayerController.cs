using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Third-person controller: WASD relative to camera, shift to run, mouse
    /// orbits. Legacy input API on purpose (no extra packages, works with
    /// default project settings).
    ///
    /// GAME FEEL PASS (game-feel-spec.md items 1-4 of "what I would build
    /// first"). What was here before had instant velocity, an instant turn,
    /// and a camera welded 5.5 metres behind the head — the three most
    /// "prototype" things about moving around LEDGER, and none of them art
    /// problems. The maths now lives in Ledger.Core.Feel where it is tested;
    /// this file is only the wiring, which is the point: a camera spring that
    /// silently becomes frame-rate dependent is invisible in a screenshot and
    /// obvious in the hands.
    public class PlayerController : MonoBehaviour
    {
        public const float WalkSpeed = (float)Locomotion.WalkSpeed;
        public const float RunSpeed = (float)Locomotion.RunSpeed;

        public bool InputLocked; // dialogue UI sets this while typing
        public Vector3? AutoMoveTarget; // sim mode drives the player via waypoints

        /// Set by GameController at spawn. Only read for the injury that
        /// drives the limp, so a null one simply means an unhurt walk.
        public GameController Game;

        readonly Locomotion _loco = new Locomotion();
        readonly CameraRig _rig = new CameraRig();

        /// Which foot. Alternating stride length IS the limp.
        int _footfall;
        float _sinceStep;
        float _bobPhase;

        /// 0 = unhurt. Read from the harm system once a second — injuries do
        /// not change between frames and Hurts() allocates.
        float _severity;
        float _severityCheckedAt = -99f;

        CharacterController _cc;
        Camera _camera;

        /// The camera this controller drives. Exposed so the car can take it
        /// over while the player is sitting in one — there is exactly one camera
        /// in this game and two things that want to move it.
        public Camera Eye => _camera;

        float _yaw = 0f;
        float _pitch = 18f;
        float _verticalVelocity;

        public static PlayerController Spawn(Vector3 position)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = "Player";
            Object.Destroy(go.GetComponent<Collider>()); // CharacterController replaces it
            go.transform.position = position;
            go.GetComponent<Renderer>().material.color = new Color(0.85f, 0.8f, 0.7f);

            var cc = go.AddComponent<CharacterController>();
            cc.height = 1.8f;
            cc.radius = 0.35f;
            cc.center = Vector3.zero;

            var player = go.AddComponent<PlayerController>();

            var camGo = new GameObject("MainCamera");
            camGo.tag = "MainCamera";
            player._camera = camGo.AddComponent<Camera>();
            camGo.AddComponent<AudioListener>();

            player._cc = cc;
            return player;
        }

        /// How hurt the player is, 0..1, straight off the harm system. The
        /// injury has been simulated since the harm system landed and never
        /// once shown; this is the wire that finally connects it to the body.
        float Severity()
        {
            if (Time.time - _severityCheckedAt < 1f) return _severity;
            _severityCheckedAt = Time.time;
            _severity = Game == null ? 0f
                : (float)Gait.SeverityFromCapability(Game.Harm.Capability("player", Game.Now.Day));
            return _severity;
        }

        void Update()
        {
            if (_camera == null || _cc == null) return;
            float dt = Time.deltaTime;
            if (dt <= 0) return;

            float severity = Severity();

            // InputLocked exists only to suppress manual WASD/mouse while a UI panel
            // is focused. Sim mode drives the player through AutoMoveTarget and is the
            // authority — it must move even when a panel (e.g. the API-key prompt) is
            // up, or the self-test player freezes and exercises nothing.
            if (!InputLocked || AutoMoveTarget.HasValue)
            {
                Vector3 want;
                bool running = false;
                if (AutoMoveTarget.HasValue)
                {
                    want = AutoMoveTarget.Value - transform.position;
                    want.y = 0;
                    // Ease off on approach so the sim player settles onto a
                    // waypoint instead of jittering across it. Momentum makes
                    // overshoot possible in a way instant velocity never did.
                    float far = want.magnitude;
                    if (far > 0.001f) want /= far;
                    want *= Mathf.Clamp01(far / 2f);
                    _yaw += 20f * dt; // slow camera sweep for varied screenshots
                }
                else
                {
                    // The sensitivity slider existed in Options, was saved, was
                    // loaded, and was multiplied by nothing: these two numbers
                    // were hardcoded. An accessibility control that does not
                    // reach the thing it names is worse than no control.
                    float sens = GameSettings.Current.MouseSensitivity;
                    _yaw += Input.GetAxis("Mouse X") * 2.5f * sens;
                    _pitch = Mathf.Clamp(_pitch - Input.GetAxis("Mouse Y") * 2f * sens, -10f, 60f);

                    var forward = Quaternion.Euler(0, _yaw, 0) * Vector3.forward;
                    var right = Quaternion.Euler(0, _yaw, 0) * Vector3.right;
                    want = forward * Input.GetAxisRaw("Vertical") + right * Input.GetAxisRaw("Horizontal");
                    if (want.sqrMagnitude > 1f) want.Normalize();
                    running = Input.GetKey(KeyCode.LeftShift);
                }

                // A hurt man is slower. Bounded in Core, because a player who
                // cannot move is a player who has stopped playing.
                float top = (running ? RunSpeed : WalkSpeed) * (float)Gait.SpeedFactor(severity);

                _loco.Step(want.x, want.z, top, dt);
                float speed = (float)_loco.Speed;

                // The body turns over time and the velocity carries — you lean
                // into a start and settle out of a stop.
                transform.rotation = Quaternion.Euler(0, (float)_loco.FacingDegrees, 0);

                _verticalVelocity = _cc.isGrounded ? -1f : _verticalVelocity - 18f * dt;
                var vel = new Vector3((float)_loco.VelocityX, _verticalVelocity, (float)_loco.VelocityZ);
                _cc.Move(vel * dt);

                Footsteps(speed, severity, dt);
                _bobPhase += speed * dt * 3.2f;
            }
            else
            {
                // Locked mid-stride: settle rather than freeze on the spot.
                _loco.Step(0, 0, WalkSpeed, dt);
                if (_loco.Speed > 0.01)
                {
                    _verticalVelocity = _cc.isGrounded ? -1f : _verticalVelocity - 18f * dt;
                    _cc.Move(new Vector3((float)_loco.VelocityX, _verticalVelocity,
                                         (float)_loco.VelocityZ) * dt);
                }
            }

            DriveCamera(dt);
        }

        /// Footsteps at your own pace: cadence comes from distance actually
        /// covered, so running is faster steps rather than the same steps
        /// played faster — and a limp is a LOPSIDED cadence, which the ear
        /// reads as an injury without being told.
        void Footsteps(float speed, float severity, float dt)
        {
            if (SimMode.Days != 0 || !_cc.isGrounded || speed < 0.15f)
            {
                _sinceStep = (float)Gait.StrideMetres * 0.6f;  // land promptly on moving off
                return;
            }
            _sinceStep += speed * dt;
            float stride = (float)Gait.StrideFor(_footfall, severity);
            if (_sinceStep < stride) return;
            _sinceStep -= stride;
            Audio.Footstep((float)Gait.StepWeight(_footfall, severity), Weather.Wetness);
            _footfall++;
        }

        /// The camera follows, it is not welded on: spring lag, FOV that opens
        /// with speed, look-ahead into the direction of travel, head bob, and
        /// a collision sweep so it slides along a wall instead of ending up
        /// inside it.
        void DriveCamera(float dt)
        {
            float effort = (float)_loco.Effort(RunSpeed);

            var pivot = transform.position + Vector3.up * 1.5f;
            var flat = new Vector3((float)_loco.VelocityX, 0, (float)_loco.VelocityZ);
            if (flat.sqrMagnitude > 0.0001f) flat.Normalize();

            _rig.Follow(pivot.x, pivot.y, pivot.z, effort, flat.x, flat.z, dt);
            var target = new Vector3((float)_rig.X, (float)_rig.Y, (float)_rig.Z);

            // Head bob is applied to the CAMERA, not the body, and is small.
            // This is the line between "alive" and "seasick".
            float bob = Mathf.Sin(_bobPhase) * (float)Gait.BobAmplitude(effort);
            target.y += bob;

            var wanted = Quaternion.Euler(_pitch, _yaw, 0) * new Vector3(0, 0, -5.5f);
            var desired = target + wanted;

            // Slide rather than clip. A sphere sweep, not a ray, because a ray
            // squeezes the camera through a gap the near plane does not fit.
            if (Physics.SphereCast(target, 0.28f, (desired - target).normalized,
                                   out var hit, wanted.magnitude,
                                   ~0, QueryTriggerInteraction.Ignore))
                desired = target + (desired - target).normalized * Mathf.Max(1.2f, hit.distance - 0.1f);

            _camera.transform.position = desired;
            _camera.transform.LookAt(target);
            _camera.fieldOfView = (float)_rig.Fov;
        }

        /// YOU ARE NOT A GHOST (game-feel-spec.md §5).
        ///
        /// CharacterController reports every wall it slides along too, so the
        /// filter matters: only bodies, only above a speed, and only once per
        /// person per second — a controller pressed against someone reports a
        /// hit every single frame, and a stumble per frame is a seizure.
        readonly Dictionary<int, float> _lastBump = new Dictionary<int, float>();

        void OnControllerColliderHit(ControllerColliderHit hit)
        {
            if (hit.collider == null) return;
            var npc = hit.collider.GetComponent<NpcWalker>();
            if (npc == null) return;

            float speed = (float)_loco.Speed;
            if (speed < Bumps.MinSpeed) return;

            int id = npc.GetInstanceID();
            if (_lastBump.TryGetValue(id, out var last) && Time.time - last < 1f) return;
            _lastBump[id] = Time.time;

            npc.Bumped(npc.transform.position - transform.position, speed);
            if (SimMode.Days == 0)
                Audio.Footstep(Bumps.Classify(speed) == BumpReaction.Brush ? 0.5f : 1.3f,
                               Weather.Wetness);
        }

        /// Called when the car hands the camera back, so the spring resumes
        /// from where the player actually is. CameraRig also cuts on any move
        /// larger than a stride, so this is belt and braces rather than the
        /// only defence.
        public void ResumeCamera()
        {
            var pivot = transform.position + Vector3.up * 1.5f;
            _rig.Place(pivot.x, pivot.y, pivot.z);
        }
    }
}
