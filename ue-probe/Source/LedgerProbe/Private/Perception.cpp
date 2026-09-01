#include "Perception.h"
#include <cmath>

namespace LedgerCore
{
	double Perception::MotionFactor(double MetresPerSecond)
	{
		if (MetresPerSecond <= 0.05)      return 0.5;  // standing still
		if (MetresPerSecond >= RunPace())  return 2.0;  // flat out
		// A walk sits at exactly 1.0 and the ends interpolate, so there is no
		// cliff where slowing from a jog to a fast walk halves your exposure.
		return MetresPerSecond <= WalkPace()
			? 0.5 + 0.5 * (MetresPerSecond - 0.05) / (WalkPace() - 0.05)
			: 1.0 + 1.0 * (MetresPerSecond - WalkPace()) / (RunPace() - WalkPace());
	}

	double Perception::ConeWeight(double DegreesOffAxis)
	{
		const double A = std::fabs(DegreesOffAxis);
		if (A <= AcuityDegrees / 2.0) return 1.0;
		if (A <= FovDegrees / 2.0)    return 0.35;
		return 0.0;
	}

	double Perception::LightFactor(double LightLevel)
	{
		const double L = Clamp01(LightLevel);
		// 0 -> 0.12 (a doorway), 0.25 -> ~0.34, 0.5 -> ~0.55, 1 -> 1.0.
		return Clamp(0.12 + 0.88 * std::pow(L, 0.78), 0.12, 1.0);
	}

	bool Perception::InSight(double Metres, double DegreesOffAxis, double LightLevel,
	                         bool bOccluded, double SubjectSpeed)
	{
		if (bOccluded) return false;
		if (SubjectSpeed < 0.0) SubjectSpeed = WalkPace();
		const double W = ConeWeight(DegreesOffAxis);
		if (W <= 0.0) return false;
		// The peripheral band is motion-only. A still subject at the edge of
		// vision is not seen, however lit they are.
		if (W < 1.0 && SubjectSpeed < StillBelow) return false;
		return Metres <= DetectRangeMetres * LightFactor(LightLevel);
	}

	int Perception::IdRung(double Metres, double LightLevel, double Familiarity,
	                       bool bHasDistinguishingMark, bool bFaceToward)
	{
		const double F = LightFactor(LightLevel);
		int Best = 0;
		if (Metres <= Rung1SilhouetteMetres * F) Best = 1;
		if (bHasDistinguishingMark && Metres <= Rung2MarkMetres * F) Best = 2;
		// A face has to be pointed at you. A limp does not, which is why rung
		// 2 survives a subject walking away and rung 3 does not.
		if (bFaceToward && Metres <= Rung3FaceMetres * F) Best = 3;
		if (Familiarity >= RecognitionFamiliarity && Metres <= Rung4RecogniseMetres * F) Best = 4;
		return Best;
	}

	bool Perception::FacingIsReadable(double Metres, double LightLevel)
	{
		return Metres <= FacingReadableMetres * LightFactor(LightLevel);
	}

	bool Perception::SymmetryPredictsSeen(double Metres, double DegreesOffAxis,
	                                      double LightOnYou, double LightOnThem,
	                                      bool bOccluded)
	{
		// TWO LIGHTS, NOT ONE. Reading his facing needs light on HIM; his
		// seeing you needs light on YOU. Collapsing them makes the rule lie in
		// the case that matters most.
		if (!FacingIsReadable(Metres, LightOnThem)) return false;
		return InSight(Metres, DegreesOffAxis, LightOnYou, bOccluded);
	}
}
