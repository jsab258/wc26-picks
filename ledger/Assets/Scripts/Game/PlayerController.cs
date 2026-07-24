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

        CharacterController _cc;
        Camera _camera;
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

            if (!InputLocked)
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
                    _yaw += Input.GetAxis("Mouse X") * 2.5f;
                    _pitch = Mathf.Clamp(_pitch - Input.GetAxis("Mouse Y") * 2f, -10f, 60f);

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
            }

            // Camera follows behind and above, looking at the head.
            var pivot = transform.position + Vector3.up * 1.5f;
            var camOffset = Quaternion.Euler(_pitch, _yaw, 0) * new Vector3(0, 0, -5.5f);
            _camera.transform.position = pivot + camOffset;
            _camera.transform.LookAt(pivot);
        }
    }
}
