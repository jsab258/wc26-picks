using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// WHO SAW IT — weapons-spec Phase 2, the half no test can stand in for.
    ///
    /// `Core/Observe.Resolve` has been complete and heavily tested since
    /// Phase 1: give it a `Deed` and a `Vantage` and it produces slots, a
    /// rung, a certainty and a willingness. What has never existed is the
    /// thing that turns a real street into a `Vantage` — where each person
    /// actually stood, which way they were facing, how much light was on the
    /// actor as opposed to on the victim, and whether a building was between
    /// them.
    ///
    /// That is the whole of this file, and it is deliberately the only thing
    /// in it. Every number it hands to Core comes from the same source the
    /// rest of the game reads: `Perceivers.LevelAt` for light,
    /// `Perceivers.Occluded` for walls, `Perceivers.OffAxis` for facing,
    /// `Perceivers.AmbientFloorAt` for the masking floor. Nothing here
    /// re-derives a threshold, because a second copy of a threshold is how
    /// the wet-road value drifted from itself.
    ///
    /// SEPARATE SIGHTLINES, and this is the part that would be easy to get
    /// lazily wrong. `Vantage.Both` exists for the common case where actor
    /// and victim are close enough that one sightline serves — and using it
    /// everywhere would make *act, no actor* unreachable, which is precisely
    /// the perception the model was rebuilt to express. So each witness gets
    /// two independent sightlines and `Both` is not used here at all.
    public static class Witnesses
    {
        /// Beyond this nobody is asked. Well past `Perception`'s own sight
        /// and hearing limits — the model decides who actually got anything,
        /// and this only stops the loop asking three hundred people about a
        /// thing that happened in another district.
        public const float ConsiderMetres = 80f;

        /// How far off the actor's own facing a witness can stand and still
        /// be looking at a face. Ninety degrees either side of straight
        /// ahead: a person half-turned toward you is still recognisable, and
        /// somebody behind your shoulder is not.
        public const float FaceArcDegrees = 90f;

        /// Everything the last deed produced, keyed by witness. Kept so the
        /// mill, the delivery window and the sim gate all read one answer
        /// rather than each recomputing it.
        public static readonly List<Observation> Last = new List<Observation>();

        public static string LastEventId { get; private set; }
        public static int Considered { get; private set; }
        public static int Saw { get; private set; }

        public static void Reset() { Last.Clear(); Considered = Saw = 0; LastEventId = null; }

        /// One sightline, built from the world rather than from an argument.
        ///
        /// `light` is measured AT THE TARGET and not at the witness, which is
        /// the whole reason a man in a doorway can watch somebody fall under
        /// a lamp and not be seen doing it.
        static Sight SightTo(Transform eye, Vector3 target)
        {
            if (eye == null) return Sight.Blind;
            return Sight.At(
                Vector3.Distance(eye.position, target),
                Perceivers.LevelAt(target),
                Perceivers.OffAxis(eye, target),
                Perceivers.Occluded(eye.position, target));
        }

        /// Resolve one deed against everybody near enough to be asked.
        ///
        /// `familiarityOf` answers how well a given witness knows the actor,
        /// 0..1 — passed in rather than looked up here because the social
        /// graph belongs to the game state and this file is geometry.
        public static List<Observation> Resolve(Deed deed, Transform actor, Vector3 victimAt,
                                                System.Func<NpcWalker, double> familiarityOf = null)
        {
            if (actor == null) { Reset(); return Last; }
            Vector3 actorAt = actor.position;
            Last.Clear();
            LastEventId = deed.EventId;
            Considered = Saw = 0;

            var eyeHeight = Vector3.up * 1.6f;
            var actorHead = actorAt + eyeHeight;
            var victimHead = victimAt + eyeHeight;

            foreach (var npc in Object.FindObjectsByType<NpcWalker>(FindObjectsSortMode.None))
            {
                if (npc == null) continue;
                float toEvent = Vector3.Distance(npc.transform.position, victimAt);
                if (toEvent > ConsiderMetres) continue;
                Considered++;

                var eye = npc.transform;
                var v = new Vantage
                {
                    WitnessId = npc.DisplayName,
                    ToActor = SightTo(eye, actorHead),
                    ToVictim = SightTo(eye, victimHead),
                    Familiarity = familiarityOf != null ? familiarityOf(npc) : 0.0,
                    AmbientFloor = Perceivers.AmbientFloorAt(eye.position, Perceivers.PresentNearby),
                    // A FACE IS TOWARD YOU WHEN YOU ARE IN FRONT OF IT, and
                    // this is computed rather than assumed. The first draft
                    // hardcoded it under a comment saying it was derived —
                    // and `FaceToward` feeds `Perception.IdRung` directly, so
                    // a constant here decides identification for the whole
                    // street. Assuming true makes everybody reach rung 4;
                    // assuming false makes a man staring straight at you
                    // unable to name you.
                    FaceToward = Vector3.Angle(actor.forward,
                                               eye.position - actorAt) < FaceArcDegrees,
                    // ALREADY LOOKING, or not. `Perception.NoticeSeconds` is a
                    // real gate in Resolve: a witness who was not watching
                    // gets nothing from their eyes however close they stand.
                    // Somebody already tracking the player has been looking;
                    // everybody else is mid-stride and has not.
                    SecondsWatching = npc.Stance >= StanceKind.Watches ? 3.0 : 0.0,
                    Alertness = npc.Stance >= StanceKind.Watches ? 0.5 : 0.0,
                    ArrivedLater = false,
                };

                var o = Observe.Resolve(deed, v);
                Last.Add(o);
                if (!o.Empty) Saw++;
            }
            return Last;
        }

        /// How many distinct slot sets the witnesses produced.
        ///
        /// §4.7's first claim is that one event and four witnesses at four
        /// positions produce FOUR DIFFERENT slot sets, and it is a claim about
        /// the world rather than about the resolver — CoreTests can prove the
        /// resolver distinguishes vantages it is handed, and only a running
        /// street can prove the vantages themselves differ. So this is the
        /// number the sim gate reads.
        public static int DistinctSlotSets()
        {
            var seen = new HashSet<Slot>();
            foreach (var o in Last) seen.Add(o.Slots);
            return seen.Count;
        }

        /// The best identification anybody got, 0..4. Reported rather than
        /// gated on: a street where nobody is close enough to reach rung 4 is
        /// a legitimate outcome and sometimes the interesting one.
        public static int BestRung()
        {
            int best = 0;
            foreach (var o in Last) if (o.Rung > best) best = o.Rung;
            return best;
        }
    }
}
