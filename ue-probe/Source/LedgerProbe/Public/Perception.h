// TRANSLITERATION of ledger/Assets/Scripts/Core/Perception.cs, D1 probe.
//
// TRANSLITERATION, NOT REWRITE, and the distinction is the whole method: the
// C# suite is the behavioural definition, so every constant and every branch
// here matches its source line for line, and where the C# is subtle the
// comment explaining why travels with it. A port that "improved" something
// would make the two engines incomparable, which is the one thing D1 must
// not allow.
//
// SCOPE: the smallest real slice. Perception.cs is 462 lines and carries no
// Unity type at all, which is why it is the honest first port; this header
// took the vision half first, enough to produce a real edit-build-test cycle
// and a test that must agree with C# exactly.
//
// SCOPE, EXTENDED 8 September by the crime ruling
// (game-design/decision-2026-09-08-the-crime-the-witness-and-the-overheard-
// consequence.md section 1 item 1): the HEARING half that Observe.Resolve
// reads. Named there line by line, and nothing else from Perception.cs came
// with it. Attention, IdentifySeconds, RingDraw, HeardAs, BelievedAt and
// Traces are OUT OF SCOPE and are not here.
#pragma once

#include "CoreMinimal.h"

namespace LedgerCore
{
	// From Feel.cs: the pace constants Perception reads through Locomotion.
	// Inlined rather than ported as a second type, because the probe measures
	// a cycle and every extra file is cycle time that is not evidence.
	constexpr double WalkSpeed = 4.0;
	constexpr double RunSpeed  = 7.0;

	inline double Clamp01(double V) { return V < 0.0 ? 0.0 : (V > 1.0 ? 1.0 : V); }
	inline double Clamp(double V, double Lo, double Hi) { return V < Lo ? Lo : (V > Hi ? Hi : V); }

	struct Perception
	{
		static constexpr double FovDegrees            = 120.0;
		static constexpr double AcuityDegrees         =  60.0;
		static constexpr double DetectRangeMetres     =  40.0;
		static constexpr double Rung1SilhouetteMetres =  35.0;
		static constexpr double Rung2MarkMetres       =  18.0;
		static constexpr double Rung3FaceMetres       =   8.0;
		// RECOGNITION REACHES FURTHER THAN A FACE. The most characteristic
		// number in the project: at twenty metres in the rain a stranger is a
		// shape and your neighbour is you.
		static constexpr double Rung4RecogniseMetres  =  25.0;
		static constexpr double RecognitionFamiliarity =  0.35;
		static constexpr double StillBelow             =  0.35;
		static constexpr double FacingReadableMetres   = 18.0;

		// Perception.cs 65. Seconds of continuous presence in the acuity band
		// before a glance becomes a look. Observe.Resolve gates every sighting
		// on it, which is why it is here and IdentifySeconds (66 to 69, the
		// identification clock) is not: nothing in scope reads that one.
		static constexpr double NoticeSeconds = 0.35;

		// ---------------------------------------------------------------
		// HEARING. Perception.cs 220 to 364, the half Observe.Resolve reads.
		//
		// Ambient floors, dB-like units, AT THE LISTENER. Spec section 16.2.
		// The listener's floor rather than the source's is the whole trick: it
		// is what lets a shot inside a loud bar still be heard by the quiet
		// street outside once the wall has taken its cut.
		//
		// ONLY THE TWO FLOORS THE CRIME RUN USES ARE HERE, by the ruling's
		// list: AmbientNight3am (227) and AmbientDaytimeStreet (228).
		// AmbientMarketNoon, AmbientBarBusy and AmbientRainAdds (229 to 232)
		// were not named and are not ported, so a caller cannot reach for one
		// here and quietly invent a condition this probe never ran.
		static constexpr double AmbientNight3am      = 15.0;
		static constexpr double AmbientDaytimeStreet = 45.0;

		// Event loudnesses, Perception.cs 243 and 244. These are the second
		// draft: the first put a walking footstep at 20 against a 3am floor of
		// 25, which made footsteps INAUDIBLE IN A SILENT STREET and flatly
		// contradicted the spec's own example of the frightened man who hears
		// one behind him. Caught by re-reading, not by a test, which is the
		// argument for worked cases in a golden table.
		//
		// LoudBottleSmash is the crime run's own loudness: section 2 of the
		// ruling picks it as the nearest named sound to breaking glass rather
		// than minting a new number for a half-brick through a shop window.
		static constexpr double LoudShout       = 65.0;
		static constexpr double LoudBottleSmash = 70.0;

		// Perception.cs 252. A wall does not scale the radius, it subtracts
		// from the loudness, which is what makes occlusion compose correctly
		// with masking instead of fighting it. Matched to Acoustics.LowPassHz,
		// where a wall is a different filter rather than more distance.
		static constexpr double WallAttenuation = 22.0;

		// Perception.cs 274. Said TO somebody who is not standing next to you.
		// Speech is a sound in these same units, which is what lets the second
		// NPC's reply be overheard by a third party at all. LoudConversation
		// (272) is not in the ruling's list and is not ported.
		static constexpr double LoudRemark = 58.0;

		// Perception.cs 276 to 278. Base radius and the doubling interval:
		// r = Base * 2^((L-A)/Div).
		static constexpr double AudibleBaseMetres = 1.5;
		static constexpr double AudibleDivisor    = 8.0;
		static constexpr double AudibleCapMetres  = 250.0;

		// Perception.cs 357. An alert listener hears more. Not a separate
		// state machine: the floor drops, so the SAME arithmetic produces
		// escalation. A calm man ignores a bang two streets away; a
		// frightened one hears a footstep.
		static constexpr double AlertFloorDrop = 8.0;

		static double WalkPace() { return WalkSpeed; }
		static double RunPace()  { return RunSpeed; }

		static double MotionFactor(double MetresPerSecond);
		static double ConeWeight(double DegreesOffAxis);
		static double LightFactor(double LightLevel);
		static bool   InSight(double Metres, double DegreesOffAxis, double LightLevel,
		                      bool bOccluded, double SubjectSpeed = -1.0);
		static int    IdRung(double Metres, double LightLevel, double Familiarity,
		                     bool bHasDistinguishingMark, bool bFaceToward = true);
		static bool   FacingIsReadable(double Metres, double LightLevel);
		static bool   SymmetryPredictsSeen(double Metres, double DegreesOffAxis,
		                                   double LightOnYou, double LightOnThem,
		                                   bool bOccluded);

		// Perception.cs 290 to 297. How far a sound of this loudness carries
		// to a listener standing in this much ambient. Zero when the ambient
		// swallows it.
		//
		// Worked, so it can be checked rather than trusted, and these six are
		// the ruling's own proof list (section 8 item 3):
		//   footstep 25 @ 3am 15    ->  3.6m   (behind you, if you listen)
		//   footstep 25 @ street 45 ->    0    (nothing at all)
		//   suppressed 62 @ bar 68  ->    0    (the jukebox eats it)
		//   suppressed 62 @ 3am 15  ->   86m   (the length of the street)
		//   snub 100 @ street 45    ->  177m
		//   shout 65 @ market 58    ->  2.2m   (which is why shouting fails)
		static double AudibleRadius(double Loudness, double AmbientFloor,
		                            bool bOccluded = false);

		// Perception.cs 359 to 360.
		static double EffectiveFloor(double AmbientFloor, double Alertness);

		// Perception.cs 362 to 364.
		static bool   Heard(double Metres, double Loudness, double AmbientFloor,
		                    bool bOccluded = false, double Alertness = 0.0);
	};
}
