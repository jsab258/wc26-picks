// TRANSLITERATION of ledger/Assets/Scripts/Core/Observation.cs, D1 probe.
//
// TRANSLITERATION, NOT REWRITE, and the distinction is the whole method: the
// C# suite is the behavioural definition, so every constant and every branch
// here matches its source line for line, and where the C# is subtle the
// comment explaining why travels with it. A port that "improved" something
// would make the two engines incomparable, which is the one thing D1 must
// not allow.
//
// SCOPE, from the crime ruling section 1 item 2: Slot 23 to 42, Awareness 44
// to 59, Observation with Label 62 to 111, Sight 127 to 141, Vantage 147 to
// 200 (RungFloor kept and fed 0 by the probe), Deed 202 to 215,
// Observe.Resolve 257 to 327, Observe.CertaintyFor 334 to 349. Feel.Clamp is
// LedgerCore::Clamp, already in Perception.h.
//
// OUT OF SCOPE AND NOT HERE: Observe.DeedFor (it needs Arsenal and Weapon,
// neither of which is ported, so the crime run hand-builds its Deed and
// prints every field), Willingness, AwarenessOf, GhostAllowed, Misattribute,
// Retell, Combine, AssemblesMore, Delivery.
//
// NO UNREAL TYPE IS IN THIS FILE, deliberately, and it is the standing rule
// from 25 August: measurement arithmetic and the decisions live where the
// tests run, because this project's top layer does not compile in the
// container that writes it. The probe module supplies traces, distances and
// live world state and nothing else.
#pragma once

#include "Perception.h"

#include <string>

namespace LedgerCore
{
	// Observation.cs 23 to 42.
	//
	// THE THING THIS REPLACES IS A BOOLEAN. Every crime game asks did he see
	// it, which is why witnesses feel fake everywhere. A violent act is a
	// short sequence and a witness catches WHICHEVER PARTS their senses
	// reached. Seven slots, filled independently.
	//
	// THE SPEC'S SIX NAMED OUTCOMES ARE NOT A LIST HERE, THEY ARE LABELS FOR
	// COMMON COMBINATIONS. That distinction is the whole reason this got
	// rebuilt: enumerating outcomes means there is no way to ask whether a
	// seventh exists.
	enum class Slot
	{
		None      = 0,
		/// You following him; the argument; you waiting in the doorway.
		Precursor = 1 << 0,
		/// The weapon appearing. Vision only, and loud socially even when the
		/// weapon is silent.
		Draw      = 1 << 1,
		/// The blow, the shot, the struggle. Vision, or hearing if loud enough.
		Act       = 1 << 2,
		/// Who went down.
		Victim    = 1 << 3,
		/// Who did it: needs vision AND an identification (Observation.Rung).
		Actor     = 1 << 4,
		/// Someone leaving, fast. The most common real witness and the cheapest.
		Flight    = 1 << 5,
		/// Body, blood, a broken door, an object left behind.
		Aftermath = 1 << 6,
	};

	// C# gets these from [Flags]; C++ has to be told. The underlying values
	// are the C#'s own, so a slot set printed as an integer means the same
	// number in both engines and the verdict can print it.
	inline Slot  operator|(Slot A, Slot B) { return (Slot)((int)A | (int)B); }
	inline Slot  operator&(Slot A, Slot B) { return (Slot)((int)A & (int)B); }
	inline Slot& operator|=(Slot& A, Slot B) { A = A | B; return A; }

	// Observation.cs 44 to 59. Did each side know the other perceived them?
	// Four states, and the bottom one is a scene rather than a flag.
	enum class Awareness
	{
		/// You have a witness and no idea. THE QUIET HORROR CASE: the design
		/// deliberately gives the player nothing here, no ghost and no
		/// warning. The first you hear of it is a rumour three days later.
		NeitherKnows,
		/// You saw them see you; they did not notice you noticing. You can act.
		YouKnow,
		/// They know you saw them, and you do not. The worst one.
		TheyKnow,
		/// Eye contact across a street. He knows. You know he knows.
		Standoff,
	};

	// Observation.cs 62 to 111. One witness's take on one event.
	class Observation
	{
	public:
		std::string WitnessId;
		std::string EventId;
		Slot        Slots;

		/// Identification of the ACTOR, 0..4, from Perception.IdRung. Kept
		/// separate from the slots because knowing what happened and knowing
		/// who did it are different things, and the gap between them is where
		/// a crime game lives.
		int Rung;

		/// How sure they are. Feeds Rumor.Confidence.
		double Certainty;

		/// Whether they will SAY it, which is not the same as believing it.
		/// Observe.Willingness is out of scope, so Resolve's own constant 1.0
		/// is the only thing that ever writes this field here.
		double Willingness;

		// THE ONE RENAMED MEMBER IN THIS PORT, AND IT IS THE COMPILER'S
		// DOING. The C# field is `Awareness Awareness`, which g++ refuses:
		// "declaration of Awareness Observation::Awareness changes meaning of
		// Awareness". The type keeps the C# name and the field carries
		// State, because the alternative was renaming the enum, and the enum
		// is the thing other code says out loud.
		Awareness AwarenessState;

		/// Who they think did it. Usually the actor; sometimes somebody else
		/// entirely, which is what makes the mill's contradiction and
		/// discredit machinery mean anything.
		///
		/// NULL IS THE EMPTY STRING HERE. The C# sets AccusedId = null and
		/// tests it with string.IsNullOrEmpty, so an empty string is already
		/// one of the two values that reads as "nobody named"; std::string
		/// cannot be null and the empty string carries the same meaning
		/// through the same test.
		std::string AccusedId;

		/// How many times they have told it. Observe.Retell is out of scope,
		/// so nothing in this port increments it.
		int Retellings;

		Observation()
			: Slots(Slot::None), Rung(0), Certainty(0.0), Willingness(0.0),
			  AwarenessState(Awareness::NeitherKnows), Retellings(0)
		{
		}

		bool NamesSomebody() const { return Rung >= 4 && !AccusedId.empty(); }
		bool Has(Slot S) const { return (Slots & S) == S; }
		bool Empty() const { return Slots == Slot::None; }

		/// Observation.cs 96 to 111. The human label, for the sim report and
		/// for writing. Derived, never stored: the slots are the truth and
		/// this is a reading of them.
		std::string Label() const
		{
			if (Empty()) return "nothing";
			if (Has(Slot::Act | Slot::Victim | Slot::Actor)) return "full";
			if (Has(Slot::Act | Slot::Victim)) return "act, no actor";
			if (Has(Slot::Draw | Slot::Actor) && !Has(Slot::Act)) return "actor, no act";
			if (Has(Slot::Act) && !Has(Slot::Victim) && !Has(Slot::Actor)) return "sound only";
			if (Has(Slot::Flight) && !Has(Slot::Act)) return "flight";
			if (Has(Slot::Aftermath) && !Has(Slot::Act)) return "aftermath";
			if (Has(Slot::Precursor) && !Has(Slot::Act) && !Has(Slot::Aftermath)) return "precursor only";
			return "partial";
		}
	};

	// Observation.cs 127 to 141. What one witness's eyes get for ONE target.
	//
	// SEPARATE SIGHTLINES FOR THE ACTOR AND THE VICTIM, and this is not
	// fussiness: it is the only way the suppressed-shot case is expressible.
	// The victim is right there in the light and the shooter is twenty metres
	// away in a doorway. One distance and one light level for "the event"
	// collapses those into the same perception and makes "act, no actor"
	// unreachable. Caught by a test that asserted four witnesses produce four
	// different slot sets and got three.
	struct Sight
	{
		double Metres;
		double DegreesOffAxis;   // the witness's facing vs this target
		double LightLevel;       // at the TARGET, not at the witness
		bool   Occluded;

		Sight() : Metres(0.0), DegreesOffAxis(0.0), LightLevel(0.0), Occluded(false) {}

		static Sight At(double InMetres, double InLight,
		                double InOffAxis = 0.0, bool bInOccluded = false)
		{
			Sight S;
			S.Metres = InMetres; S.LightLevel = InLight;
			S.DegreesOffAxis = InOffAxis; S.Occluded = bInOccluded;
			return S;
		}

		/// Nothing to see: out of the world, behind a building, in the dark.
		static Sight Blind()
		{
			Sight S;
			S.Metres = 1e6; S.LightLevel = 0.0; S.Occluded = true;
			return S;
		}
	};

	// Observation.cs 147 to 200. The geometry of one witness at the moment
	// something happened. Plain data so the resolver can be tested without a
	// scene, which is exactly what lets it be tested without an ENGINE.
	struct Vantage
	{
		std::string WitnessId;
		Sight  ToActor;
		Sight  ToVictim;
		double Familiarity;      // with the actor, 0..1
		bool   ActorHasMark;     // limp, scar, a coat people know
		bool   FaceToward;       // the actor's face, toward this witness
		double AmbientFloor;     // at the witness
		double Alertness;
		double SecondsWatching;  // how long they had been looking

		/// The best identification this witness had ALREADY reached before
		/// the deed, from watching. A floor under the instantaneous rung,
		/// never a replacement for it.
		///
		/// A FLOOR, NOT A REPLACEMENT, and the asymmetry is the design.
		/// Knowing who somebody is does not decay the moment the light does:
		/// if you have already placed a face, a lamp going out does not
		/// un-place it. But standing closer than you were still IMPROVES the
		/// reading, so the instantaneous value has to be able to win.
		///
		/// FED 0 BY THIS PROBE, by the ruling: Perception.Attention is the
		/// accumulator that earns a floor and it is out of scope, so the
		/// crime run has nothing honest to put here and prints the zero.
		int RungFloor;

		bool ArrivedLater;       // found it rather than saw it

		Vantage()
			: Familiarity(0.0), ActorHasMark(false), FaceToward(false),
			  AmbientFloor(0.0), Alertness(0.0), SecondsWatching(0.0),
			  RungFloor(0), ArrivedLater(false)
		{
		}

		/// Observation.cs 186 to 199. The common case: actor and victim close
		/// enough together that one sightline serves for both. Most fights
		/// are this. Note what the C# leaves at its default here and what it
		/// sets: FaceToward true and SecondsWatching 3.0 are written in, the
		/// mark and the alertness and the rung floor are not.
		static Vantage Both(const std::string& Id, double Metres, double Light,
		                    double Familiarity, double AmbientFloor)
		{
			const Sight S = Sight::At(Metres, Light);
			Vantage V;
			V.WitnessId = Id; V.ToActor = S; V.ToVictim = S;
			V.Familiarity = Familiarity; V.AmbientFloor = AmbientFloor;
			V.FaceToward = true; V.SecondsWatching = 3.0;
			return V;
		}
	};

	// Observation.cs 202 to 215. What the event itself offers to be
	// perceived.
	struct Deed
	{
		std::string EventId;
		std::string ActorId;
		std::string VictimId;
		double Loudness;         // of the act, from Perception.Loud*
		bool VictimCriesOut;
		bool WeaponDrawn;
		bool ActorFled;
		bool LeavesBody;
		bool HadPrecursor;       // following, arguing, waiting
		bool IsAccident;         // no crime at all, unless somebody saw the push

		Deed()
			: Loudness(0.0), VictimCriesOut(false), WeaponDrawn(false),
			  ActorFled(false), LeavesBody(false), HadPrecursor(false),
			  IsAccident(false)
		{
		}
	};

	// Observation.cs 216 onward, the two members the ruling names.
	struct Observe
	{
		/// Observation.cs 257 to 327. THE GENERATOR. One event, one vantage,
		/// one slot set.
		///
		/// Each slot is filled by its own test, which is the point: nothing
		/// here consults a table of six outcomes. Four witnesses at four
		/// positions produce four different sets because they fail different
		/// tests, not because a designer enumerated the cases.
		static Observation Resolve(const Deed& InDeed, const Vantage& V)
		{
			Observation O;
			O.WitnessId = V.WitnessId;
			O.EventId   = InDeed.EventId;
			O.AccusedId = "";     // C#: AccusedId = null. See Observation.AccusedId.

			const bool bLongEnough = V.SecondsWatching >= Perception::NoticeSeconds;
			// subjectSpeed: 1.4 is the C#'s own named argument, and it is not
			// the walk pace: a person committing a deed is moving, so the
			// peripheral band's motion test can pass. Changing it would move
			// every edge-of-vision witness in the game.
			const bool bSeesActor = bLongEnough && Perception::InSight(
				V.ToActor.Metres, V.ToActor.DegreesOffAxis, V.ToActor.LightLevel,
				V.ToActor.Occluded, 1.4);
			const bool bSeesVictim = bLongEnough && Perception::InSight(
				V.ToVictim.Metres, V.ToVictim.DegreesOffAxis, V.ToVictim.LightLevel,
				V.ToVictim.Occluded, 1.4);

			// Hearing, which gives direction and distance and never identity.
			// Measured to the act, which happens where the victim is.
			const bool bHeardAct = InDeed.Loudness > 0
				&& Perception::Heard(V.ToVictim.Metres, InDeed.Loudness, V.AmbientFloor,
				                     V.ToVictim.Occluded, V.Alertness);
			const bool bHeardCry = InDeed.VictimCriesOut
				&& Perception::Heard(V.ToVictim.Metres, Perception::LoudShout, V.AmbientFloor,
				                     V.ToVictim.Occluded, V.Alertness);

			if (V.ArrivedLater)
			{
				// Someone who walked into it afterwards gets the aftermath and
				// nothing else: no act, no actor, however close they now are.
				if (InDeed.LeavesBody || !InDeed.IsAccident) O.Slots |= Slot::Aftermath;
				O.Certainty = 0.9;
				O.Willingness = 1.0;
				return O;
			}

			if (bSeesActor && InDeed.HadPrecursor) O.Slots |= Slot::Precursor;
			if (bSeesActor && InDeed.WeaponDrawn) O.Slots |= Slot::Draw;
			if (bSeesVictim || bHeardAct || bHeardCry) O.Slots |= Slot::Act;
			if (bSeesVictim) O.Slots |= Slot::Victim;
			if (bSeesActor && InDeed.ActorFled) O.Slots |= Slot::Flight;

			// THE ACTOR SLOT IS NOT THE ACT SLOT, and it is resolved off its
			// own sightline. Seeing a man drop and knowing who dropped him are
			// two different perceptions of two different people standing in
			// two different places, which is the whole of the suppressed
			// pistol case, and it falls out rather than being written in.
			if (bSeesActor)
			{
				O.Rung = Perception::IdRung(V.ToActor.Metres, V.ToActor.LightLevel,
				                            V.Familiarity, V.ActorHasMark, V.FaceToward);
				// WHAT THEY HAD ALREADY WORKED OUT, as a floor.
				//
				// ONLY WHEN THEY CAN STILL SEE THE ACTOR. Inside this branch
				// on purpose: a floor that applied to somebody who cannot see
				// the actor at all would let a witness name a man they never
				// looked at, which is the suppressed-pistol case running
				// backwards and a far worse bug than the one it fixes.
				if (V.RungFloor > O.Rung) O.Rung = V.RungFloor;
				if (O.Rung >= 1) O.Slots |= Slot::Actor;
				if (O.Rung >= 4) O.AccusedId = InDeed.ActorId;
			}

			O.Certainty = CertaintyFor(O.Slots, O.Rung, bSeesVictim || bSeesActor, bHeardAct);
			O.Willingness = 1.0;
			return O;
		}

		/// Observation.cs 334 to 349. Confidence, from what they got rather
		/// than from a constant.
		///
		/// Capped below 0.95 for anything short of a full sighting, because
		/// GossipMill promotes at 0.95 into hard knowledge and a partial
		/// observation must never become a thing somebody KNOWS.
		static double CertaintyFor(Slot Slots, int Rung, bool bLooked, bool bHeard)
		{
			if (Slots == Slot::None) return 0;
			double C = 0.20;
			if ((int)(Slots & Slot::Act) != 0) C += bHeard && !bLooked ? 0.20 : 0.40;
			if ((int)(Slots & Slot::Victim) != 0) C += 0.20;
			if ((int)(Slots & Slot::Aftermath) != 0) C += 0.25;
			if ((int)(Slots & Slot::Actor) != 0) C += 0.06 * Rung;
			// THE CAP HAS TO BE REACHABLE OR IT IS DECORATION. A break run
			// raised it to 1.0 and every test still passed, which meant no
			// observation had ever come near it: the components summed to
			// 0.85 at best. They now sum past it for a full close sighting,
			// so the clamp is the thing actually holding a witness below the
			// mill's 0.95 promotion threshold rather than a comment claiming
			// to.
			return Clamp(C, 0.05, 0.94);
		}
	};
}
