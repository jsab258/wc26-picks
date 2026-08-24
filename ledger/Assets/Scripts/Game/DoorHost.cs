using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE DOORS ACTUALLY SWING NOW.
    ///
    /// `Core/DoorSwing` is a damped spring with an overshoot, a latch that
    /// catches at the very end of closing and a thump at the open stop. It
    /// is tested, it is thoughtful, and until 24 Aug NOTHING IN THE GAME
    /// REFERENCED IT — the reach ledger carried the whole class as unwired
    /// with the note WIRE: M17. Rule 6, on the object its own comment calls
    /// the most-touched in any game.
    ///
    /// This is the missing half and nothing more: the geometry gets a hinge
    /// (see `WorldBuilder`'s door leaf), and this ticks the spring and puts
    /// its angle on the transform.
    ///
    /// A DOORWAY, NOT A SPHERE, and the first version of this was a sphere.
    /// A 2.2m radius sounds modest until you notice a British pavement is
    /// about three metres wide and every shopfront door is on it, so walking
    /// down Copper Row would have swung the entire street open like a guard
    /// of honour. What makes a door open is APPROACHING IT, which needs the
    /// door's facing and not just its position: the player must be in front
    /// of the leaf (`outward` positive), close along that normal, and within
    /// half a doorway of its centreline. Walking past two feet away fails the
    /// lateral test and nothing moves, which is the behaviour a street needs.
    ///
    /// PROXIMITY, NOT AN INTERACT VERB. A door that needs a keypress is a
    /// second design decision and this one only claims the first. The bands
    /// are bands and not thresholds — 1.9m out and 0.9m lateral to open,
    /// 2.8m and 1.5m to close — so somebody standing on the line does not
    /// make the door flutter.
    ///
    /// ONLY THE UNSETTLED ARE INTEGRATED. 376 doors times a spring every
    /// frame is a cost with nothing to show for it, and `DoorSwing.AtRest`
    /// exists to say so in its own words: "settled at either stop, so
    /// callers know when to stop simulating". `TickedPeak` is the count that
    /// actually integrated in a frame, and it is printed beside `Count`
    /// because a spring that never runs and a street with no doors read
    /// identically otherwise (rule 3b).
    ///
    /// The player's own position drives it; the crowd does not open doors,
    /// which is a deliberate limit rather than an oversight — walkers do not
    /// enter buildings yet, so a door swinging for one would be a lie.
    ///
    /// A STATIC TICK, NOT A MonoBehaviour, and that is the whole reason
    /// this class exists in the shape it does. A component nothing attaches
    /// is precisely the fault being repaired here — `DoorSwing` sat unwired
    /// for a milestone — and writing the fix as a component I would then
    /// have to remember to add is walking into it from the other side.
    /// `BlobShadow.Tick` is the pattern: one call site, in the loop that
    /// already runs.
    public static class DoorHost
    {
        struct Leaf
        {
            public Transform Hinge;
            public DoorSwing Swing;
            public Vector3 At;
            /// The way the door faces, horizontal and unit length.
            public Vector3 Out;
            /// THE HINGE IS A ROOT OBJECT, so its local rotation IS its world
            /// rotation, and writing `Euler(0, angle, 0)` onto it would throw
            /// away the `LookRotation(outward)` `WorldBuilder` gave it — every
            /// door on an east-facing wall snapping ninety degrees the instant
            /// it first swung. The swing is a rotation RELATIVE to how the
            /// door hangs, so the resting pose is kept and multiplied.
            public Quaternion Base;
        }

        static readonly List<Leaf> _leaves = new List<Leaf>();

        /// How many doors exist, how many have swung this run, how many
        /// latched, how many hit the open stop, and the most that needed
        /// integrating in any one frame. Zero swung with a non-zero count is
        /// a wire that never fired, and reads nothing like a street with no
        /// doors (rule 3b).
        public static int Count, Swung, Latches, Stops, TickedPeak;

        public static void Register(Transform hinge)
        {
            if (hinge == null) return;
            var fwd = hinge.forward; fwd.y = 0f;
            if (fwd.sqrMagnitude < 1e-4f) fwd = Vector3.forward;
            _leaves.Add(new Leaf
            {
                Hinge = hinge,
                Swing = new DoorSwing(),
                At = hinge.position,
                Out = fwd.normalized,
                Base = hinge.localRotation,
            });
            Count = _leaves.Count;
        }

        /// Cleared per BUILD, like every counter in WorldBuilder — a static
        /// list that survives a rebuild would tick the previous town's doors
        /// and hold their transforms alive.
        public static void Reset()
        {
            _leaves.Clear();
            Count = Swung = Latches = Stops = TickedPeak = 0;
        }

        public static void Tick(float dt)
        {
            if (_leaves.Count == 0 || dt <= 0f) return;
            var who = PlayerController.Where;
            if (!who.HasValue) return;
            var p = who.Value;
            int ticked = 0;

            for (int i = 0; i < _leaves.Count; i++)
            {
                var leaf = _leaves[i];
                if (leaf.Hinge == null) continue;
                var d = p - leaf.At; d.y = 0f;
                // Past the far edge of the band it is shut and staying shut,
                // so it costs a distance test and nothing else.
                if (d.sqrMagnitude > 40f * 40f)
                {
                    if (leaf.Swing.Open) leaf.Swing.Set(false);
                    continue;
                }

                // How far out from the face, and how far off the centreline.
                float outward = Vector3.Dot(d, leaf.Out);
                float lateral = (d - leaf.Out * outward).magnitude;

                bool inDoorway = outward > 0f && outward < 1.9f && lateral < 0.9f;
                bool away = outward > 2.8f || outward < -0.2f || lateral > 1.5f;
                if (inDoorway && !leaf.Swing.Open) { leaf.Swing.Set(true); Swung++; Audio.Ui("door"); }
                else if (away && leaf.Swing.Open) { leaf.Swing.Set(false); Audio.Ui("door"); }

                // Settled at a stop with nothing pulling it: the spring has
                // nothing left to say. This is also what keeps `Latched` from
                // re-firing — it is cleared inside `Tick`, so a skipped door
                // must not have its flags read either, and `continue` here is
                // before both reads on purpose.
                if (leaf.Swing.AtRest) continue;

                ticked++;
                leaf.Swing.Tick(dt);
                // The latch is a small metal catch and the stop is the leaf
                // hitting its frame; both go through `Impact`, which is
                // material-matched, pitch-varied and BUDGETED — the one bus
                // that can refuse a sound when the street is busy.
                if (leaf.Swing.Latched) { Latches++; Audio.Impact("metal", 0.30f); }
                if (leaf.Swing.HitStop) { Stops++; Audio.Impact("wood", 0.55f); }
                leaf.Hinge.localRotation =
                    leaf.Base * Quaternion.Euler(0f, (float)leaf.Swing.Angle, 0f);
            }

            if (ticked > TickedPeak) TickedPeak = ticked;
        }
    }
}
