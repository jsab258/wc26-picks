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
// takes the vision half, enough to produce a real edit-build-test cycle and
// a test that must agree with C# exactly.
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
	};
}
