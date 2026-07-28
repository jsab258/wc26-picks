using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The place you are standing in, as a sound (game-feel-spec.md §4).
    ///
    /// "Nothing sells a PLACE faster" than the alley sounding like an alley.
    /// The trick here is that we did not have to author a single acoustic
    /// volume to get it: the street network already distinguishes a
    /// four-metre lane between two building faces from an eight-metre
    /// avenue, and that distinction — authored for pathfinding — is exactly
    /// the distinction the ear makes.
    ///
    /// ONE reverb zone, parented to the listener, with its settings driven
    /// from wherever the listener happens to be. The obvious alternative is a
    /// zone per lane, which is dozens of objects doing the work of one and
    /// leaves seams at every boundary. Here there are no boundaries: the
    /// settings lerp, so walking out of an alley is a fade and not a cut,
    /// which is §8's rule about no hard cuts anywhere.
    public class RoomTone : MonoBehaviour
    {
        static RoomTone _instance;
        AudioReverbZone _zone;
        Transform _ear;
        float _nextProbe;

        /// Where the listener currently is. Read by anything that wants to
        /// know whether it is under a sky or between two walls.
        public static SpaceKind Current { get; private set; } = SpaceKind.Outdoors;

        public static void Ensure(Transform ear)
        {
            if (_instance != null || ear == null) return;
            var go = new GameObject("RoomTone");
            go.transform.SetParent(ear, false);
            _instance = go.AddComponent<RoomTone>();
            _instance._ear = ear;
            _instance.Build();
        }

        void Build()
        {
            _zone = gameObject.AddComponent<AudioReverbZone>();
            _zone.reverbPreset = AudioReverbPreset.User;
            // Huge radii: the zone travels with the listener, so it is always
            // "inside" and its parameters — not its geometry — carry the room.
            _zone.minDistance = 500f;
            _zone.maxDistance = 1000f;
            Apply(SpaceKind.Outdoors, 1f);
        }

        void Update()
        {
            if (_ear == null || _zone == null) return;

            // Twice a second is plenty. Which side of a lane you are on does
            // not change at frame rate, and NearestOnStreet walks the edges.
            if (Time.time >= _nextProbe)
            {
                _nextProbe = Time.time + 0.5f;
                var p = _ear.position;
                Current = StreetMap.NearestOnStreet(p.x, p.z, out var ox, out var oz, out var edge)
                    ? Acoustics.SpaceFor(edge != null ? edge.Kind : null,
                          Mathf.Sqrt((float)((p.x - ox) * (p.x - ox) + (p.z - oz) * (p.z - oz))))
                    : SpaceKind.Outdoors;
            }

            // Lerp rather than switch: stepping out of an alley should be a
            // fade, not a cut.
            Apply(Current, Time.deltaTime * 2.5f);
        }

        void Apply(SpaceKind space, float t)
        {
            float wet = (float)Acoustics.Wetness(space);
            float decay = (float)Acoustics.DecaySeconds(space);
            float room = (float)Acoustics.RoomMetres(space);

            // Unity's room/reverb are millibels: -10000 is silence, 0 is full.
            // A linear wetness maps onto that curve far better through a
            // square root than directly, or everything below "very wet"
            // collapses into inaudible.
            _zone.room = (int)Mathf.Lerp(_zone.room, Mathf.Lerp(-2200f, -200f, Mathf.Sqrt(wet)), t);
            _zone.decayTime = Mathf.Lerp(_zone.decayTime, decay, t);
            // Pre-delay is how the ear judges size: the further the first
            // reflection has to travel, the bigger the place sounds. Sound
            // covers about a third of a metre per millisecond.
            _zone.reflectionsDelay = Mathf.Lerp(_zone.reflectionsDelay, room / 343f, t);
            // A narrow hard space is BRIGHT; a big soft one is not. Without
            // this every space is the same colour and only differs in length,
            // which is why generic reverb sounds like a preset.
            _zone.roomHF = (int)Mathf.Lerp(_zone.roomHF, space == SpaceKind.Alley ? -200f : -1400f, t);
        }
    }
}
