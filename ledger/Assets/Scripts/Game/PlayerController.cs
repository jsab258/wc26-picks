using UnityEngine;

namespace Ledger.Game
{
    /// Minimal third-person controller: WASD relative to camera, shift to run,
    /// mouse orbits the camera. Uses the legacy input API on purpose (no extra
    /// packages, works with default project settings).
    public class PlayerController : MonoBehaviour
    {
        public const float WalkSpeed = 4f;
        public const float RunSpeed = 7f;

        public bool InputLocked; // dialogue UI sets this while typing
        public Vector3? AutoMoveTarget; // sim mode drives the player via waypoints

        /// Metres between footfalls. Roughly a real stride, so the cadence reads
        /// as a person walking rather than as a metronome under the camera.
        const float StrideMetres = 1.6f;
        float _sinceStep;

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

        void Update()
        {
            if (_camera == null || _cc == null) return;

            // InputLocked exists only to suppress manual WASD/mouse while a UI panel
            // is focused. Sim mode drives the player through AutoMoveTarget and is the
            // authority — it must move even when a panel (e.g. the API-key prompt) is
            // up, or the self-test player freezes and exercises nothing.
            if (!InputLocked || AutoMoveTarget.HasValue)
            {
                Vector3 move;
                if (AutoMoveTarget.HasValue)
                {
                    move = AutoMoveTarget.Value - transform.position;
                    move.y = 0;
                    if (move.sqrMagnitude > 1f) move.Normalize();
                    _yaw += 20f * Time.deltaTime; // slow camera sweep for varied screenshots
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
                    move = forward * Input.GetAxisRaw("Vertical") + right * Input.GetAxisRaw("Horizontal");
                    if (move.sqrMagnitude > 1f) move.Normalize();
                }

                float speed = Input.GetKey(KeyCode.LeftShift) ? RunSpeed : WalkSpeed;
                if (move.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation,
                        Quaternion.LookRotation(move), 12f * Time.deltaTime);

                _verticalVelocity = _cc.isGrounded ? -1f : _verticalVelocity - 18f * Time.deltaTime;
                _cc.Move((move * speed + Vector3.up * _verticalVelocity) * Time.deltaTime);

                // Footsteps at your own pace: the step cadence comes from the
                // distance actually covered, so running is faster steps rather
                // than the same steps played faster. Silent in sim mode, where
                // nobody is listening and a step per frame is just noise.
                if (SimMode.Days == 0 && _cc.isGrounded && move.sqrMagnitude > 0.001f)
                {
                    _sinceStep += speed * Time.deltaTime;
                    if (_sinceStep >= StrideMetres) { _sinceStep = 0f; Audio.Footstep(); }
                }
                else _sinceStep = StrideMetres * 0.6f;  // land the first step promptly on moving off
            }

            // Camera follows behind and above, looking at the head.
            var pivot = transform.position + Vector3.up * 1.5f;
            var camOffset = Quaternion.Euler(_pitch, _yaw, 0) * new Vector3(0, 0, -5.5f);
            _camera.transform.position = pivot + camOffset;
            _camera.transform.LookAt(pivot);
        }
    }
}
