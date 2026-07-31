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
                // THE VICTIM IS NOT A BYSTANDER, and this loop counted them as
                // one. They stand at distance zero with a clear sightline, so
                // they resolved to a full sighting every time — which means
                // `Saw` could never be zero for any act at all, and a killing
                // in an empty alley had one witness: the man on the ground.
                //
                // `Reaction.AsVictim` owns the target's account and always
                // has; it is the function that knows a dead man is not a
                // witness, and combat-spec §2's whole trade turns on that. Two
                // paths were producing the victim's view, one of them wrong,
                // and Phase 3 is what made it visible — nothing before this
                // ever asked whether a specific place had NO witnesses.
                if (npc.DisplayName == deed.VictimId) continue;
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

        // ---- THE DELIVERY WINDOW ------------------------------------------
        //
        // §4.7's fourth claim: a witness intercepted before delivery leaves NO
        // trace in the mill; the same witness intercepted a minute later
        // leaves an indelible one. That gap is the mechanic the whole phase
        // exists for — the player can follow, talk, pay, threaten, help or
        // kill, and every one of those is itself an act somebody else can
        // observe.
        //
        // `Core/Delivery` owns the timing and the once-only arrival. This
        // owns the list, the ticking, and the one thing Core must not know:
        // that arriving means filing into the gossip mill.

        public static readonly List<Delivery> InFlight = new List<Delivery>();

        public static int Started { get; private set; }
        public static int Arrived { get; private set; }
        public static int Interceptions { get; private set; }

        /// Below this nobody carries it anywhere. An observation of nothing
        /// is not a thing to report, and a witness who will not speak is the
        /// best lever in the design rather than a failure of the model.
        public const double TellsAtWillingness = 0.5;

        public static void ResetDeliveries()
        {
            InFlight.Clear();
            Started = Arrived = Interceptions = 0;
            Retellings = HardenedToAName = 0;
        }

        /// Everybody who got something and will say it starts walking.
        ///
        /// `walkMinutesFor` is how long this witness needs to reach the place
        /// they are taking it to — real pathing distance, supplied by the
        /// caller, because the map belongs to the game and this file is the
        /// window rather than the route.
        public static int Dispatch(IEnumerable<Observation> observations,
                                   string destinationId,
                                   System.Func<Observation, double> walkMinutesFor,
                                   System.Func<Observation, double> nerveOf = null)
        {
            int began = 0;
            foreach (var o in observations)
            {
                if (o == null || o.Empty) continue;
                if (o.Willingness < TellsAtWillingness) continue;
                double nerve = nerveOf != null ? nerveOf(o) : 0.5;
                InFlight.Add(Delivery.Begin(o.WitnessId, destinationId,
                                            walkMinutesFor(o), nerve, o.Willingness));
                began++;
                Started++;
            }
            return began;
        }

        /// Advance every delivery by `minutes` of game time, and file the ones
        /// that arrive.
        ///
        /// INDELIBLE ON ARRIVAL, which is the sharp edge of claim 4 and the
        /// reason the window matters at all: once it is told to somebody whose
        /// job is to remember, nothing the player does afterwards takes it
        /// back. Before arrival, an interception leaves the mill untouched —
        /// not a weakened rumour, not a doubt. Nothing.
        public static int Tick(double minutes, GossipMill mill, GameTime now,
                               System.Func<Delivery, Fact> factFor,
                               System.Func<Delivery, string> summaryFor)
        {
            if (minutes <= 0 || InFlight.Count == 0) return 0;
            int arrived = 0;
            for (int i = InFlight.Count - 1; i >= 0; i--)
            {
                var d = InFlight[i];
                if (!d.Tick(minutes))
                {
                    if (!d.InFlight) InFlight.RemoveAt(i);
                    continue;
                }
                arrived++;
                Arrived++;
                if (mill != null && factFor != null)
                    mill.Witness(d.DestinationId, factFor(d), summaryFor?.Invoke(d),
                                 sensitive: true, now: now, confidence: 0.9, indelible: true);
                InFlight.RemoveAt(i);
            }
            return arrived;
        }

        /// Paid, threatened, talked round, or killed — and it only works
        /// before they get there. Returns false when they already arrived,
        /// which is the answer the player has to live with.
        public static bool Intercept(string witnessId)
        {
            for (int i = 0; i < InFlight.Count; i++)
            {
                if (InFlight[i].WitnessId != witnessId) continue;
                if (!InFlight[i].Intercept()) return false;
                InFlight.RemoveAt(i);
                Interceptions++;
                return true;
            }
            return false;
        }

        // ---- MEMORY HARDENS AS IT DECAYS ----------------------------------
        //
        // A hesitant "a big man in a long coat" becomes, after a week of
        // telling it, a certain "it was Tom Novak" — with no new observation,
        // purely from retelling. `Observe.Retell` has modelled that since
        // Phase 1 and nothing called it, so a witness left alone was simply
        // static, and the time pressure ran the wrong way: waiting was free.
        //
        // Waiting must not be free. A witness you do not deal with gets MORE
        // dangerous, which is what makes the delivery window a decision rather
        // than a countdown.

        public static int Retellings { get; private set; }
        public static int HardenedToAName { get; private set; }

        /// Every witness still carrying an undelivered account tells it again.
        /// Called on the game clock rather than per frame — a retelling is a
        /// conversation, not a tick.
        ///
        /// `expectedOf` supplies who this witness would name if their certainty
        /// climbs past what they actually saw. That is the mechanism by which a
        /// WRONG name gets in, and it is deliberate: climbing to a name without
        /// new evidence means the name comes from what they already believed.
        public static int RetellRound(System.Func<Observation, string> expectedOf = null)
        {
            int hardened = 0;
            foreach (var o in Last)
            {
                if (o == null || o.Empty) continue;
                bool namedBefore = o.NamesSomebody;
                Observe.Retell(o, expectedOf != null ? expectedOf(o) : null);
                Retellings++;
                if (!namedBefore && o.NamesSomebody) { hardened++; HardenedToAName++; }
            }
            return hardened;
        }

        /// COMPARING NOTES. Whether putting these two in a room produces a
        /// truth neither of them held — the thing the mill's compare-notes path
        /// has always been able to do and has never had partial information to
        /// do it with.
        ///
        /// Returns the number of PAIRS that would assemble more, which is the
        /// honest measure: one pair is a coincidence of geometry, several means
        /// the street is genuinely producing partial accounts that fit together.
        public static int PairsThatAssembleMore()
        {
            int pairs = 0;
            for (int i = 0; i < Last.Count; i++)
                for (int j = i + 1; j < Last.Count; j++)
                    if (Observe.AssemblesMore(Last[i], Last[j])) pairs++;
            return pairs;
        }

        /// How many witnesses can put a NAME to it, rather than a description.
        /// The difference between a rumour and an accusation.
        public static int NamingWitnesses()
        {
            int n = 0;
            foreach (var o in Last) if (o != null && o.NamesSomebody) n++;
            return n;
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
