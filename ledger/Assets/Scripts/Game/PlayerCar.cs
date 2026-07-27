using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The car you can drive (roadmap M12, step 6).
    ///
    /// Arcade and deliberately shallow: get in, drive, get out. Accelerate,
    /// brake, steer, reverse. No gears, no damage, no fuel, no handbrake
    /// physics. The player asked for a city that feels real, not for a driving
    /// game, and every hour spent on a tyre model is an hour not spent on the
    /// thing this project is actually about.
    ///
    /// What it IS for, beyond getting across the district faster: a car is a
    /// thing witnesses describe. Driving to a job is quicker and more memorable
    /// than walking to one, and the coat does not hide a vehicle. That trade —
    /// speed against a harder-edged description in somebody's mouth tomorrow —
    /// is the reason this is in a crime game rather than a driving one.
    ///
    /// Kinematic, not rigidbody. The AI traffic is stepped by Core against its
    /// own rules; dropping a physics body into the middle of that would produce
    /// two systems arguing about the same metre of road. The car refuses to
    /// enter buildings using the same mass test the walkers use, and it exists
    /// to the AI as a hazard, so traffic brakes for it the way it brakes for a
    /// person.
    public class PlayerCar : MonoBehaviour
    {
        public const float MaxSpeed = 13.5f;      // ~50 km/h; the district is small
        public const float ReverseSpeed = 4.5f;
        public const float Accel = 7.0f;
        public const float BrakeRate = 14.0f;
        public const float Drag = 3.2f;
        public const float TurnRate = 95f;        // degrees/sec at speed
        public const float EnterRange = 3.2f;

        public static PlayerCar Instance { get; private set; }
        public bool Occupied { get; private set; }
        public float Speed { get; private set; }

        /// What a witness calls it. Read from the same catalogue the AI traffic
        /// uses, so the player's car is described in the city's own vocabulary.
        public static VehicleKind Kind => VehicleKinds.Car;

        PlayerController _driver;
        Camera _camera;
        float _yaw;
        Vector3 _exitOffset = new Vector3(-1.6f, 0, 0);

        public static PlayerCar Spawn(Vector3 where, float heading)
        {
            var root = new GameObject("PlayerCar");
            root.transform.position = where;
            root.transform.rotation = Quaternion.Euler(0, heading, 0);

            var car = root.AddComponent<PlayerCar>();
            car._yaw = heading;

            float len = (float)Kind.Length, wid = (float)Kind.Width;
            Part(root.transform, "body", new Vector3(0, 0.42f, 0), new Vector3(wid, 0.6f, len), AssetLibrary.Metal);
            Part(root.transform, "cabin", new Vector3(0, 0.85f, -len * 0.06f),
                new Vector3(wid * 0.88f, 0.5f, len * 0.46f), AssetLibrary.Glass);
            foreach (var side in new[] { -1f, 1f })
            {
                var lamp = Part(root.transform, side < 0 ? "lampL" : "lampR",
                    new Vector3(side * wid * 0.32f, 0.45f, len / 2f - 0.1f),
                    new Vector3(0.22f, 0.16f, 0.08f), AssetLibrary.Window);
                WorldBuilder.RegisterNightLight(lamp.GetComponent<Renderer>());
            }

            Instance = car;
            return car;
        }

        static Transform Part(Transform parent, string name, Vector3 local, Vector3 size, string material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(material);
            var col = go.GetComponent<Collider>();
            if (col != null) Destroy(col);
            return go.transform;
        }

        /// You hit somebody. The car stops hard — you do not leave this behind
        /// at forty, because the beat where the player realises what has just
        /// happened is the entire point of the system.
        public void Jolt() => Speed = Mathf.Min(Speed, 1.0f);

        public bool WithinReach(Vector3 from) =>
            (new Vector3(transform.position.x - from.x, 0, transform.position.z - from.z)).magnitude <= EnterRange;

        public void GetIn(PlayerController driver, Camera cam)
        {
            if (Occupied || driver == null) return;
            _driver = driver;
            _camera = cam;
            Occupied = true;
            Speed = 0f;
            driver.gameObject.SetActive(false);
            Audio.Ui("door");
        }

        public void GetOut()
        {
            if (!Occupied) return;
            Occupied = false;
            Speed = 0f;
            if (_driver != null)
            {
                // Step out onto whichever side is not inside a wall.
                var here = transform.position;
                var left = here + transform.rotation * _exitOffset;
                var right = here + transform.rotation * new Vector3(-_exitOffset.x, 0, 0);
                var spot = WorldBuilder.SegmentClear(here, left) ? left : right;
                spot.y = here.y + 0.9f;
                _driver.transform.position = spot;
                _driver.gameObject.SetActive(true);
            }
            Audio.Ui("door");
            _driver = null;
        }

        void Update()
        {
            if (!Occupied || _camera == null) return;

            float throttle = Input.GetAxisRaw("Vertical");
            float steer = Input.GetAxisRaw("Horizontal");

            if (throttle > 0.01f) Speed += Accel * throttle * Time.deltaTime;
            else if (throttle < -0.01f)
                Speed += (Speed > 0 ? BrakeRate : Accel) * throttle * Time.deltaTime;
            else
                Speed = Mathf.MoveTowards(Speed, 0f, Drag * Time.deltaTime);
            Speed = Mathf.Clamp(Speed, -ReverseSpeed, MaxSpeed);

            // Steering authority scales with speed: a stationary car does not
            // pirouette, which is the single tell that separates "arcade" from
            // "a box sliding around on a floor".
            float authority = Mathf.Clamp01(Mathf.Abs(Speed) / 4f);
            _yaw += steer * TurnRate * authority * Mathf.Sign(Speed) * Time.deltaTime;
            transform.rotation = Quaternion.Euler(0, _yaw, 0);

            var step = transform.forward * (Speed * Time.deltaTime);
            var next = transform.position + step;
            // The same mass test the walkers use. Driving into a building stops
            // you dead rather than putting the camera inside a wall — there is no
            // damage model to express it any other way, and a wall you can drive
            // through undoes the city more than a hard stop does.
            if (WorldBuilder.SegmentClear(transform.position, next, inflate: 1.4f))
                transform.position = next;
            else
                Speed = 0f;

            // The player IS where the car is. Their body is switched off while
            // they are sitting in it, but every proximity check in the game —
            // barks, gates, the night drop, the crowd's level of detail — reads
            // their transform, and a driver whose position is frozen at the kerb
            // where they got in would be able to drive across the district while
            // the world quietly believed they had not moved. It also makes the
            // interesting thing possible: driving TO a job, and being seen
            // arriving in a car.
            if (_driver != null)
                _driver.transform.position = new Vector3(transform.position.x, 0.9f, transform.position.z);

            var pivot = transform.position + Vector3.up * 1.6f;
            var offset = Quaternion.Euler(12f, _yaw, 0) * new Vector3(0, 0, -8.5f);
            _camera.transform.position = pivot + offset;
            _camera.transform.LookAt(pivot);
        }

        /// Where a witness would say the car was standing.
        public string AddressNow() => StreetMap.AddressOf(transform.position.x, transform.position.z);
    }
}
