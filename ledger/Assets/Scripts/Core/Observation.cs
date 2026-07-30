using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// WHAT A WITNESS ACTUALLY GOT. Stage 2 of the pipeline, and the join
    /// between the tactical layer and the social one.
    ///
    /// THE THING THIS REPLACES is a boolean. Every crime game asks *did he see
    /// it*, which is why witnesses feel fake everywhere. A violent act is a
    /// short sequence — you follow him in, you draw, you use it, he goes down,
    /// you leave, the body lies there — and a witness catches WHICHEVER PARTS
    /// their senses reached. Seven slots, filled independently.
    ///
    /// THE SPEC'S SIX NAMED OUTCOMES ARE NOT A LIST HERE, THEY ARE LABELS FOR
    /// COMMON COMBINATIONS. That distinction is the whole reason this got
    /// rebuilt: v2 of the spec enumerated six outcomes I had invented, which
    /// meant there was no way to ask whether a seventh existed. A generator
    /// produces cases nobody thought of — *precursor only*, useless alone and
    /// devastating when a second witness supplies the aftermath and the two of
    /// them talk.
    [Flags]
    public enum Slot
    {
        None = 0,
        /// You following him; the argument; you waiting in the doorway.
        Precursor = 1 << 0,
        /// The weapon appearing. Vision only, and loud socially even when the
        /// weapon is silent.
        Draw = 1 << 1,
        /// The blow, the shot, the struggle. Vision, or hearing if loud enough.
        Act = 1 << 2,
        /// Who went down.
        Victim = 1 << 3,
        /// Who did it — needs vision AND an identification (`Observation.Rung`).
        Actor = 1 << 4,
        /// Someone leaving, fast. The most common real witness and the cheapest.
        Flight = 1 << 5,
        /// Body, blood, a broken door, an object left behind.
        Aftermath = 1 << 6,
    }

    /// Did each side know the other perceived them? Four states, and the
    /// bottom one is a scene rather than a flag.
    public enum Awareness
    {
        /// You have a witness and no idea. THE QUIET HORROR CASE, and the
        /// design deliberately gives the player nothing here — no ghost, no
        /// warning. The first you hear of it is a rumour three days later.
        NeitherKnows,
        /// You saw them see you; they did not notice you noticing. You can act.
        YouKnow,
        /// They know you saw them, and you do not. The worst one, and the game
        /// must allow it.
        TheyKnow,
        /// Eye contact across a street. He knows. You know he knows.
        Standoff,
    }

    /// One witness's take on one event.
    public class Observation
    {
        public string WitnessId;
        public string EventId;
        public Slot Slots;

        /// Identification of the ACTOR, 0..4 — `Perception.IdRung`. Kept
        /// separate from the slots because knowing what happened and knowing
        /// who did it are different things, and the gap between them is where
        /// a crime game lives.
        public int Rung;

        /// How sure they are. Feeds `Rumor.Confidence`.
        public double Certainty;

        /// Whether they will SAY it — which is not the same as believing it,
        /// and is the best lever in the design. A man who saw you because he
        /// was somewhere he should not have been is a witness who will not
        /// come forward, and the route to safety is finding out why he was on
        /// Hook Street at two in the morning.
        public double Willingness;

        public Awareness Awareness = Awareness.NeitherKnows;

        /// Who they think did it. Usually the actor; sometimes somebody else
        /// entirely (§4.6), which is what makes the mill's contradiction and
        /// discredit machinery mean anything.
        public string AccusedId;

        /// How many times they have told it. Drives hardening — see `Retell`.
        public int Retellings;

        public bool NamesSomebody => Rung >= 4 && !string.IsNullOrEmpty(AccusedId);
        public bool Has(Slot s) => (Slots & s) == s;
        public bool Empty => Slots == Slot.None;

        /// The human label, for the sim report and for writing. Derived, never
        /// stored — the slots are the truth and this is a reading of them.
        public string Label()
        {
            if (Empty) return "nothing";
            if (Has(Slot.Act | Slot.Victim | Slot.Actor)) return "full";
            if (Has(Slot.Act | Slot.Victim)) return "act, no actor";
            if (Has(Slot.Draw | Slot.Actor) && !Has(Slot.Act)) return "actor, no act";
            if (Has(Slot.Act) && !Has(Slot.Victim) && !Has(Slot.Actor)) return "sound only";
            if (Has(Slot.Flight) && !Has(Slot.Act)) return "flight";
            if (Has(Slot.Aftermath) && !Has(Slot.Act)) return "aftermath";
            if (Has(Slot.Precursor) && !Has(Slot.Act) && !Has(Slot.Aftermath)) return "precursor only";
            return "partial";
        }
    }

    /// What one witness's eyes get for ONE target.
    ///
    /// SEPARATE SIGHTLINES FOR THE ACTOR AND THE VICTIM, and this is not
    /// fussiness — it is the only way Jafar's own example is expressible. A
    /// suppressed shot in a crowded street: the victim is right there in the
    /// light and the shooter is twenty metres away in a doorway. One distance
    /// and one light level for "the event" collapses those into the same
    /// perception and makes *act, no actor* unreachable.
    ///
    /// Caught by a test that asserted four witnesses produce four different
    /// slot sets and got three — the far witness was resolving identically to
    /// the close one because the model had no way to say *I saw him fall and
    /// not who did it*.
    public struct Sight
    {
        public double Metres;
        public double DegreesOffAxis;   // the witness's facing vs this target
        public double LightLevel;       // at the TARGET, not at the witness
        public bool Occluded;

        public static Sight At(double metres, double light,
                               double offAxis = 0, bool occluded = false) =>
            new Sight { Metres = metres, LightLevel = light,
                        DegreesOffAxis = offAxis, Occluded = occluded };

        /// Nothing to see: out of the world, behind a building, in the dark.
        public static Sight Blind => new Sight { Metres = 1e6, LightLevel = 0, Occluded = true };
    }

    /// The geometry of one witness at the moment something happened. Plain
    /// data so the resolver can be tested without a scene.
    public struct Vantage
    {
        public string WitnessId;
        public Sight ToActor;
        public Sight ToVictim;
        public double Familiarity;      // with the actor, 0..1
        public bool ActorHasMark;       // limp, scar, a coat people know
        public bool FaceToward;         // the actor's face, toward this witness
        public double AmbientFloor;     // at the witness
        public double Alertness;
        public double SecondsWatching;  // how long they had been looking
        public bool ArrivedLater;       // found it rather than saw it

        /// The common case: actor and victim close enough together that one
        /// sightline serves for both. Most fights are this.
        public static Vantage Both(string id, double metres, double light,
                                   double familiarity, double ambientFloor)
        {
            var sight = Sight.At(metres, light);
            return new Vantage
            {
                WitnessId = id, ToActor = sight, ToVictim = sight,
                Familiarity = familiarity, AmbientFloor = ambientFloor,
                FaceToward = true, SecondsWatching = 3.0,
            };
        }
    }

    /// What the event itself offers to be perceived.
    public struct Deed
    {
        public string EventId;
        public string ActorId;
        public string VictimId;
        public double Loudness;         // of the act — `Perception.Loud*`
        public bool VictimCriesOut;
        public bool WeaponDrawn;
        public bool ActorFled;
        public bool LeavesBody;
        public bool HadPrecursor;       // following, arguing, waiting
        public bool IsAccident;         // no crime at all, unless somebody saw the push
    }

    public static class Observe
    {
        /// BUILD A DEED FROM A WEAPON, so the perceptible facts of an act come
        /// from the weapon table and nowhere else.
        ///
        /// EXISTS TO CLOSE A HOLE RATHER THAN TO SAVE TYPING. Without it the
        /// Unity layer has to hand `Resolve` a loudness, a cries-out flag and a
        /// leaves-a-body flag, which means those three numbers get typed out a
        /// second time at every call site — and this project has already
        /// watched a wet-road threshold drift apart from its own copy. One
        /// source, and the source is `Arsenal`.
        public static Deed DeedFor(Weapon w, string eventId, string actorId,
                                   string victimId, bool actorFled = false,
                                   bool hadPrecursor = false)
        {
            if (w == null) return new Deed { EventId = eventId, ActorId = actorId,
                                            VictimId = victimId };
            return new Deed
            {
                EventId = eventId,
                ActorId = actorId,
                VictimId = victimId,
                Loudness = w.Loudness,
                VictimCriesOut = w.VictimCriesOut,
                // An accident has no draw — there is nothing to see appearing,
                // which is most of why it reads as an accident.
                WeaponDrawn = w.Family != Family.Environment && w.ReadySeconds > 0,
                ActorFled = actorFled,
                LeavesBody = w.LeavesBody,
                HadPrecursor = hadPrecursor,
                IsAccident = Arsenal.IsAccident(w),
            };
        }

        /// THE GENERATOR. One event, one vantage, one slot set.
        ///
        /// Each slot is filled by its own test, which is the point — nothing
        /// here consults a table of six outcomes. Four witnesses at four
        /// positions produce four different sets because they fail different
        /// tests, not because a designer enumerated the cases.
        public static Observation Resolve(Deed deed, Vantage v)
        {
            var o = new Observation
            {
                WitnessId = v.WitnessId,
                EventId = deed.EventId,
                AccusedId = null,
            };

            bool longEnough = v.SecondsWatching >= Perception.NoticeSeconds;
            bool seesActor = longEnough && Perception.InSight(
                v.ToActor.Metres, v.ToActor.DegreesOffAxis, v.ToActor.LightLevel,
                v.ToActor.Occluded, subjectSpeed: 1.4);
            bool seesVictim = longEnough && Perception.InSight(
                v.ToVictim.Metres, v.ToVictim.DegreesOffAxis, v.ToVictim.LightLevel,
                v.ToVictim.Occluded, subjectSpeed: 1.4);

            // Hearing, which gives direction and distance and never identity.
            // Measured to the act, which happens where the victim is.
            bool heardAct = deed.Loudness > 0
                && Perception.Heard(v.ToVictim.Metres, deed.Loudness, v.AmbientFloor,
                                    v.ToVictim.Occluded, v.Alertness);
            bool heardCry = deed.VictimCriesOut
                && Perception.Heard(v.ToVictim.Metres, Perception.LoudShout, v.AmbientFloor,
                                    v.ToVictim.Occluded, v.Alertness);

            if (v.ArrivedLater)
            {
                // Someone who walked into it afterwards gets the aftermath and
                // nothing else — no act, no actor, however close they now are.
                if (deed.LeavesBody || !deed.IsAccident) o.Slots |= Slot.Aftermath;
                o.Certainty = 0.9;
                o.Willingness = 1.0;
                return o;
            }

            if (seesActor && deed.HadPrecursor) o.Slots |= Slot.Precursor;
            if (seesActor && deed.WeaponDrawn) o.Slots |= Slot.Draw;
            if (seesVictim || heardAct || heardCry) o.Slots |= Slot.Act;
            if (seesVictim) o.Slots |= Slot.Victim;
            if (seesActor && deed.ActorFled) o.Slots |= Slot.Flight;

            // THE ACTOR SLOT IS NOT THE ACT SLOT, and it is resolved off its
            // own sightline. Seeing a man drop and knowing who dropped him are
            // two different perceptions of two different people standing in
            // two different places — which is the whole of the suppressed-
            // pistol case, and it now falls out rather than being written in.
            if (seesActor)
            {
                o.Rung = Perception.IdRung(v.ToActor.Metres, v.ToActor.LightLevel,
                                           v.Familiarity, v.ActorHasMark, v.FaceToward);
                if (o.Rung >= 1) o.Slots |= Slot.Actor;
                if (o.Rung >= 4) o.AccusedId = deed.ActorId;
            }

            o.Certainty = CertaintyFor(o.Slots, o.Rung, seesVictim || seesActor, heardAct);
            o.Willingness = 1.0;
            return o;
        }

        /// Confidence, from what they got rather than from a constant.
        ///
        /// Capped below 0.95 for anything short of a full sighting, because
        /// `GossipMill` promotes at 0.95 into hard knowledge and a partial
        /// observation must never become a thing somebody KNOWS.
        public static double CertaintyFor(Slot slots, int rung, bool looked, bool heard)
        {
            if (slots == Slot.None) return 0;
            double c = 0.20;
            if ((slots & Slot.Act) != 0) c += heard && !looked ? 0.20 : 0.40;
            if ((slots & Slot.Victim) != 0) c += 0.20;
            if ((slots & Slot.Aftermath) != 0) c += 0.25;
            if ((slots & Slot.Actor) != 0) c += 0.06 * rung;
            // THE CAP HAS TO BE REACHABLE OR IT IS DECORATION. A break run
            // raised it to 1.0 and every test still passed, which meant no
            // observation had ever come near it: the components summed to 0.85
            // at best. They now sum past it for a full close sighting, so the
            // clamp is the thing actually holding a witness below the mill's
            // 0.95 promotion threshold rather than a comment claiming to.
            return Feel.Clamp(c, 0.05, 0.94);
        }

        /// WILL THEY SAY IT. Separate from believing it, and driven by things
        /// the project already simulates.
        ///
        /// `ownSecret` is the lever the whole design points at: a witness who
        /// was somewhere they should not have been has a reason of their own
        /// to stay quiet, and finding that reason is a better answer than a
        /// knife. That is the game's thesis expressed inside the violence
        /// system rather than beside it.
        public static double Willingness(double nerve, double loyaltyToPlayer,
                                         double ownSecret, double fearOfOutfit,
                                         double sympathyForVictim)
        {
            // Tuned so the top of the range does NOT saturate: a maximally
            // willing witness sits just under 1.0, because a value that
            // clamps hides every difference above it and the first draft did
            // exactly that — two very different witnesses both read 1.00.
            double w = 0.45
                     + 0.35 * Feel.Clamp01(nerve)
                     + 0.35 * Feel.Clamp01(sympathyForVictim)
                     - 0.55 * Feel.Clamp01(loyaltyToPlayer)
                     - 0.85 * Feel.Clamp01(ownSecret)      // the strongest lever, deliberately
                     - 0.45 * Feel.Clamp01(fearOfOutfit);
            return Feel.Clamp01(w);
        }

        /// Mutual awareness, from two perception results. Costs nothing to
        /// detect because both records already exist.
        public static Awareness AwarenessOf(bool youSawThem, bool theySawYou)
        {
            if (youSawThem && theySawYou) return Awareness.Standoff;
            if (youSawThem) return Awareness.YouKnow;
            if (theySawYou) return Awareness.TheyKnow;
            return Awareness.NeitherKnows;
        }

        /// Whether the ghost (§6.2) is allowed to appear for this observation.
        ///
        /// ONLY WHEN THE AWARENESS WAS MUTUAL. v3 of the spec showed it for
        /// every witness, which silently destroyed the quiet-horror case above
        /// — if the ghost always appears, being seen without knowing it cannot
        /// exist. Restricting it also makes it honest: it stops being a readout
        /// of another person's mind, which Tom has no right to, and becomes a
        /// picture of something the character actually experienced.
        public static bool GhostAllowed(Awareness a) =>
            a == Awareness.Standoff || a == Awareness.YouKnow;

        /// MISATTRIBUTION. A partial identification plus expectation produces a
        /// named accusation of the wrong man — a long coat, at night, near the
        /// docks is Nikos to somebody who expects Nikos.
        ///
        /// Being wrong is content: the player can be accused of something they
        /// did not do, can let a false belief stand at no implementation cost
        /// (it is the absence of an action), and can plant an impression rather
        /// than evidence.
        public static string Misattribute(Observation o, string expectedId, int seed)
        {
            if (o.Rung < 1 || o.Rung >= 4) return o.AccusedId;   // too little, or certain
            if (string.IsNullOrEmpty(expectedId)) return o.AccusedId;
            // Rung 2 is a distinguishing mark, so it misattributes less often
            // than a bare silhouette — but a coat people know is exactly the
            // kind of mark that belongs to more than one man.
            double p = o.Rung == 1 ? 0.45 : 0.25;
            return new Random(seed).NextDouble() < p ? expectedId : o.AccusedId;
        }

        /// MEMORY HARDENS AS IT DECAYS: accuracy falls, confidence rises.
        ///
        /// A hesitant *"a big man in a long coat"* becomes, after a week of
        /// telling it, a certain *"it was Tom Novak"* — with no new
        /// observation, purely from retelling. It is true of real witnesses, it
        /// makes `Discredit` interesting (you are arguing with a person's
        /// certainty rather than their honesty), and it gives time pressure in
        /// the useful direction: a witness left alone gets MORE dangerous.
        ///
        /// **Hardening never confers indelibility.** Indelible is a property of
        /// a body existing, not of anybody's certainty — otherwise a hardened
        /// false accusation would become unanswerable and §4.6's best idea
        /// would turn into a punishment.
        public const int RetellingsPerRung = 4;

        public static void Retell(Observation o, string expectedId = null)
        {
            if (o == null || o.Empty) return;
            o.Retellings++;
            o.Certainty = Feel.Clamp(o.Certainty + 0.10, 0.0, 0.94);
            if (o.Retellings % RetellingsPerRung == 0 && o.Rung < 4)
            {
                o.Rung++;
                // Climbing to a name without new evidence means the name comes
                // from what they already believed, which is how a wrong one
                // gets in. This is the mechanism, not a side effect.
                if (o.Rung >= 4 && string.IsNullOrEmpty(o.AccusedId))
                    o.AccusedId = expectedId;
            }
        }

        /// COMPARING NOTES. Two partial slot sets assembled into more than
        /// either held — the thing `CompareNotes` has always been able to do
        /// and has never had partial information to do it with.
        public static Slot Combine(params Observation[] parts) =>
            parts.Where(p => p != null).Aggregate(Slot.None, (acc, p) => acc | p.Slots);

        /// Does putting these two in a room produce a truth neither had?
        public static bool AssemblesMore(Observation a, Observation b)
        {
            if (a == null || b == null) return false;
            Slot both = a.Slots | b.Slots;
            return both != a.Slots && both != b.Slots;
        }
    }

    /// A WITNESS IS A DEADLINE, not a flag.
    ///
    /// Between observing and the street knowing, the witness is a person
    /// walking somewhere with a purpose. Who they pick is characterisation —
    /// a constable, Ellis, the victim's brother, their own kitchen — and
    /// unlike RDR2's abstract lawman ours is a named person with a schedule.
    ///
    /// The window is the point: the player can follow, talk, pay, threaten,
    /// help or kill, and every one of those is itself an act somebody else can
    /// observe. Threatening a witness in front of a second witness is how a
    /// manageable night becomes a catastrophe.
    public class Delivery
    {
        public string WitnessId;
        public string DestinationId;
        public double MinutesRemaining;
        public bool Running;
        public bool Arrived;
        public bool Intercepted;

        /// A frightened witness runs and picks the nearest destination; an
        /// unsure one sits with it for the best part of an hour first.
        public static Delivery Begin(string witnessId, string destinationId,
                                     double walkMinutes, double nerve, double willingness)
        {
            bool frightened = nerve < 0.35;
            double delay = willingness < 0.5 ? 20 + 70 * (1 - willingness) : 0;
            return new Delivery
            {
                WitnessId = witnessId,
                DestinationId = destinationId,
                Running = frightened,
                MinutesRemaining = Math.Max(0.5, walkMinutes * (frightened ? 0.45 : 1.0) + delay),
            };
        }

        /// Returns true on the tick it arrives — exactly once, so a caller
        /// cannot file the same observation twice by ticking again.
        public bool Tick(double minutes)
        {
            if (Arrived || Intercepted || !(minutes > 0)) return false;
            MinutesRemaining -= minutes;
            if (MinutesRemaining > 0) return false;
            MinutesRemaining = 0;
            Arrived = true;
            return true;
        }

        /// Paid, threatened, talked round, or killed. Before arrival this
        /// leaves no trace in the mill at all; after it, nothing helps.
        public bool Intercept()
        {
            if (Arrived) return false;
            Intercepted = true;
            return true;
        }

        public bool InFlight => !Arrived && !Intercepted;
    }
}
