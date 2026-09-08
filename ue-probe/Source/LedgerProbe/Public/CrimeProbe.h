// THE CRIME, THE WITNESS AND THE OVERHEARD CONSEQUENCE, ON -LedgerCrime.
//
// Ruling: game-design/decision-2026-09-08-the-crime-the-witness-and-the-
// overheard-consequence.md, clause by clause. One entry point, armed from
// StartupModule when the command line carries -LedgerCrime and never
// otherwise, exactly as -LedgerWalk is (WalkProbe.h, LedgerProbe.cpp).
// ALedgerGameMode::InitGame has never heard of -LedgerCrime, so a crime run
// falls through to the SAME branch a genuine human launch takes: the default
// ALedgerCharacter spawns, collision is on, and
// LedgerVignetteShot::BuildInteractiveStreet runs unmodified. A plain launch
// with no switch is bit-for-bit unaffected.
//
// WHY THE DECISIONS AND THE STRINGS ARE IN THIS HEADER AND NOT IN THE .cpp.
// The standing rule from 25 August (.claude/rules/instruments.md): this
// project's top layer does not compile in the container that writes it, so a
// formatter written there ships UNRUN, and an unrun formatter printing a
// plausible string is the quietest instrument fault there is. Everything
// below is plain C++ over the six transliterated LedgerCore headers and
// carries no Unreal type, so g++ compiles and RUNS it before any dispatch.
// CrimeProbe.cpp supplies live world state and nothing else: actors, traces,
// distances read off the engine's own transforms, screenshots and file
// writes.
//
// SELFTEST, ACCEPTING CASE FIRST. Selftest() below is the live decision path
// run on fixed inputs, and CrimeProbe.cpp calls it at Start() so its result
// is a number on the verdict rather than a claim in a comment. The rejecting
// fixtures are synthetic (a bank with no line at the asked rung, a context
// that exists nowhere), so doing the work this tool prompts can never break
// the tool.
//
// WHAT THIS FILE CANNOT SEE, said plainly: nothing here proves an actor
// spawned, that a trace hit a terrace, that a window went dark or that a
// memory file landed in a commit. Those are the run's business and the
// verdict's keys are how they are read.
#pragma once

#include "GameTime.h"
#include "Gossip.h"
#include "MemoryStore.h"
#include "Observation.h"
#include "Perception.h"
#include "Suspicion.h"

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

namespace LedgerCrime
{
	// ---- formatting primitives ------------------------------------------
	//
	// NO SPACES IN A VALUE. Every reader of this project's key=value lines
	// splits on whitespace and truncates in silence, so a value that could
	// carry a space is passed through this first and the structure is
	// carried by / and .. instead.
	inline std::string NoSpaces(const std::string& S)
	{
		std::string Out = S;
		for (std::string::size_type I = 0; I < Out.size(); ++I)
		{
			if (Out[I] == ' ' || Out[I] == '\t' || Out[I] == '\n' || Out[I] == '\r') { Out[I] = '-'; }
		}
		if (Out.empty()) { Out = "none"; }
		return Out;
	}

	inline std::string F1(double V)
	{
		char Buf[64];
		std::snprintf(Buf, sizeof(Buf), "%.1f", V);
		return std::string(Buf);
	}

	// TWO DECIMALS THE WAY THE C# WRITES THEM, not %.2f: the two disagree on
	// every binary-exact or below-half boundary and MemoryStore.h carries the
	// measurement that settled it. Used for every 2dp number here so a
	// certainty printed on the verdict and an importance written into the
	// committed memory markdown are rendered by one rule.
	inline std::string F2(double V) { return LedgerCore::FormatTwoDecimals(V); }

	inline std::string Int(int V)
	{
		char Buf[32];
		std::snprintf(Buf, sizeof(Buf), "%d", V);
		return std::string(Buf);
	}

	inline const char* YesNo(bool B) { return B ? "yes" : "no"; }

	// ---- the street frame -------------------------------------------------
	//
	// x along the street, y up, z across, exactly as
	// production/specs/vignette-pieces.json states it. The engine's X is
	// x*100, its Y is z*100 and its Z is y*100, which is VignetteShot.cpp's
	// own SpawnPiece mapping read out of that file and not a second opinion
	// about it. Every position below is in street metres; the .cpp converts
	// once, at the engine boundary, in both directions.
	struct P3
	{
		double X, Y, Z;
		P3() : X(0.0), Y(0.0), Z(0.0) {}
		P3(double InX, double InY, double InZ) : X(InX), Y(InY), Z(InZ) {}
	};

	inline double Metres(const P3& A, const P3& B)
	{
		const double DX = A.X - B.X, DY = A.Y - B.Y, DZ = A.Z - B.Z;
		return std::sqrt(DX * DX + DY * DY + DZ * DZ);
	}

	// Vector3.Angle, which is what Witnesses.cs 152 uses and what every
	// off-axis number in the C# perception model is measured with. Degrees,
	// unsigned, 0..180. A zero-length vector answers 0 rather than a NaN.
	inline double AngleDeg(const P3& A, const P3& B)
	{
		const double LA = std::sqrt(A.X * A.X + A.Y * A.Y + A.Z * A.Z);
		const double LB = std::sqrt(B.X * B.X + B.Y * B.Y + B.Z * B.Z);
		if (LA <= 0.0 || LB <= 0.0) { return 0.0; }
		double C = (A.X * B.X + A.Y * B.Y + A.Z * B.Z) / (LA * LB);
		C = LedgerCore::Clamp(C, -1.0, 1.0);
		return std::acos(C) * 180.0 / 3.14159265358979323846;
	}

	// THE ENGINE'S YAW IS THE FILE'S YAW, no conversion, exactly as
	// VignetteShot.cpp's PlaceCamera treats the shared file's own yaw: 0
	// looks down street +x, 90 looks across to street +z.
	inline P3 ForwardFromYaw(double YawDeg)
	{
		const double R = YawDeg * 3.14159265358979323846 / 180.0;
		return P3(std::cos(R), 0.0, std::sin(R));
	}

	inline double YawToFace(const P3& From, const P3& To)
	{
		return std::atan2(To.Z - From.Z, To.X - From.X) * 180.0 / 3.14159265358979323846;
	}

	inline P3 Minus(const P3& A, const P3& B) { return P3(A.X - B.X, A.Y - B.Y, A.Z - B.Z); }

	// How far off the looker's own axis a target sits.
	inline double OffAxisDeg(const P3& Eye, double EyeYawDeg, const P3& Target)
	{
		return AngleDeg(ForwardFromYaw(EyeYawDeg), Minus(Target, Eye));
	}

	// Witnesses.cs 152, verbatim in shape: Angle(actor.forward, eye - actor)
	// against FaceArcDegrees. The number is printed beside the arc so the
	// word faceToward never has to be trusted on its own.
	inline double FaceAngleDeg(const P3& ActorAt, double ActorYawDeg, const P3& Eye)
	{
		return AngleDeg(ForwardFromYaw(ActorYawDeg), Minus(Eye, ActorAt));
	}

	// ---- the placements, ruling section 2, all printed --------------------
	//
	// A builder may move a placement within its stated constraint and prints
	// what it did. Nothing below was moved: every one is the ruling's own
	// number, and the run prints the ENGINE's reading of where the actor
	// actually ended up beside it.
	const double kEyeHeightM      = 1.6;    // Witnesses.cs eye, and the trace start
	const double kFaceArcDegrees  = 90.0;   // Witnesses.cs 43
	const double kLightLevel      = 1.0;    // Perceivers.LevelAt, overcast_day, lanterns off
	const double kAmbientFloor    = LedgerCore::Perception::AmbientDaytimeStreet;  // 45.0
	const double kFamiliarity     = 0.0;    // Witnesses.cs 142: strangers
	const double kTie             = 0.6;    // GossipDirector.cs 127 to 128
	const double kTalkRangeM      = 6.0;    // GossipDirector.cs 34, together
	const double kEarshotM        = 6.0;    // GossipDirector.cs 247, 577 to 578
	const int    kAlertness       = 0;      // no stance, nobody is watching for trouble
	const int    kRungFloor       = 0;      // Perception.Attention out of scope

	// Pawn start, the two crime points and the four standing places. Street
	// metres; the y is filled in by a DOWNWARD TRACE at the point, never
	// typed, because the east footway is cambered (its litter sits at y 0.087
	// to 0.098 against a nominal ground top of 0.075) and a typed height
	// leaves a body floating or buried.
	const double kStartX = 1.0,  kStartZ = 4.0;
	const double kCrimeAX = 6.87,  kCrimeAZ = 3.9;
	const double kCrimeBX = 12.87, kCrimeBZ = 3.9;
	const double kW1AX = 9.0,  kW1AZ = 4.7;     // P1, the next doorstep along
	const double kW1BX = 22.5, kW1BZ = -7.5;    // P2, on the yard floor
	const double kN2X  = 22.5, kN2Z  = -8.9;    // PN, behind the terrace from both
	const double kOverhearX = 22.5, kOverhearZ = -3.3;   // Y, between the cones

	// The yard floor (amendment A2): no ground plane exists in x 21..24
	// between ground_plot_2 and ground_plot_3, and that gap is the only place
	// a person can stand with a terrace between them and a shop window.
	const double kYardX = 22.5, kYardY = -0.05, kYardZ = -9.125;
	const double kYardSX = 3.0, kYardSY = 0.3,  kYardSZ = 8.0;

	// Stand-in bodies: the shape-from-code discipline LedgerCharacter.h
	// states. No Mixamo body exists in ue-probe and the verdict says so.
	const double kBodyDiameterM = 0.4, kBodyHeightM = 1.75;

	// Shards and the brick, ruling section 2.
	const double kShardSX = 0.15, kShardSY = 0.01, kShardSZ = 0.10;
	const double kBrickSX = 0.215, kBrickSY = 0.065, kBrickSZ = 0.1;
	const int    kShardsPerCrime = 8;

	// EIGHT OFFSETS FROM THE WINDOW FOOT, ALL INSIDE THE 1 m THE RULING
	// STATES AND ALL ON THE FOOTWAY SIDE (negative z, away from the shop
	// front). Fixed rather than random: a probe that scatters differently
	// every run cannot be compared with its own last frame. The selftest
	// checks every magnitude against the 1 m constraint, so the constraint is
	// a thing the tool proved rather than a thing this comment claims.
	inline int ShardOffsetCount() { return kShardsPerCrime; }
	inline void ShardOffset(int I, double& OutDX, double& OutDZ)
	{
		static const double DX[8] = { -0.62, -0.31,  0.02,  0.35,  0.66, -0.86,  0.88,  0.10 };
		static const double DZ[8] = { -0.45, -0.72, -0.55, -0.78, -0.41, -0.22, -0.18, -0.92 };
		const int J = (I < 0 || I >= 8) ? 0 : I;
		OutDX = DX[J];
		OutDZ = DZ[J];
	}

	// The brick lands INSIDE the window line, on the shop floor
	// (ground_plot_1 spans z 5.125 to 13.125 at this x), 0.315 m past the
	// glass plane at z 4.985.
	const double kBrickInsideZ = 5.30;

	// ---- timings, every one a ceiling or a duration and never a threshold --
	const double kSeqIntervalSeconds   = 0.4;   // the ruling's own sampling
	const int    kMaxSeqFrames         = 32;    // a clock cap; it announces itself
	const int    kMilestoneCount       = 6;
	const int    kForcedAtDeeds        = 4;     // one before and one after each deed
	const double kOverheardHoldSeconds = 3.0;   // section 5: about three seconds
	const double kSayAfterSeconds      = 2.1;   // GossipDirector's own i * 2.1 beat

	// ---- slots and the label ---------------------------------------------
	//
	// Bit order is the C#'s own (Observation.h 45 to 63), so the printed list
	// reads act,victim,actor,flight for a full sighting in both engines.
	inline std::string SlotsValue(LedgerCore::Slot S)
	{
		static const char* kNames[7] =
			{ "precursor", "draw", "act", "victim", "actor", "flight", "aftermath" };
		std::string Out;
		for (int I = 0; I < 7; ++I)
		{
			if (((int)S & (1 << I)) == 0) { continue; }
			if (!Out.empty()) { Out += ","; }
			Out += kNames[I];
		}
		return Out.empty() ? std::string("none") : Out;
	}

	// Observation::Label() is PROSE ("act, no actor") and a value may not
	// carry a space. The comma-space becomes / and any remaining space a -,
	// so "act, no actor" prints as act/no-actor and "full" prints unchanged.
	// The transformation is here, where the test runs, and never at a call
	// site.
	inline std::string LabelValue(const LedgerCore::Observation& O)
	{
		return NoSpaces(LedgerCore::ReplaceAll(O.Label(), ", ", "/"));
	}

	// ---- the deed ---------------------------------------------------------
	//
	// HAND-BUILT WITH EVERY FIELD PRINTED, by the ruling: Observe.DeedFor
	// needs Arsenal and Weapon, neither of which is ported, and an Arsenal
	// row for a half-brick is filed as a name rather than built here.
	inline LedgerCore::Deed MakeDeed(const std::string& EventId,
	                                 const std::string& ActorId,
	                                 const std::string& VictimId)
	{
		LedgerCore::Deed D;
		D.EventId  = EventId;
		D.ActorId  = ActorId;
		D.VictimId = VictimId;
		// The nearest NAMED sound to breaking glass rather than a new number
		// minted for a half-brick through a shop window.
		D.Loudness        = LedgerCore::Perception::LoudBottleSmash;
		D.VictimCriesOut  = false;
		D.WeaponDrawn     = false;
		D.ActorFled       = true;    // the script walks the pawn away
		D.LeavesBody      = false;
		D.HadPrecursor    = false;
		D.IsAccident      = false;
		return D;
	}

	inline std::string DeedInputsLine(const LedgerCore::Deed& D)
	{
		return "deedLoudness=" + F1(D.Loudness)
		     + " deedVictimCriesOut=" + YesNo(D.VictimCriesOut)
		     + " deedWeaponDrawn=" + YesNo(D.WeaponDrawn)
		     + " deedActorFled=" + YesNo(D.ActorFled)
		     + " deedLeavesBody=" + YesNo(D.LeavesBody)
		     + " deedHadPrecursor=" + YesNo(D.HadPrecursor)
		     + " deedIsAccident=" + YesNo(D.IsAccident)
		     + " deedVictimId=" + NoSpaces(D.VictimId)
		     + " deedSource=hand-built/Observe.DeedFor-needs-Arsenal-not-ported";
	}

	// ---- one witness at one crime -----------------------------------------
	//
	// Every field above the line is MEASURED by CrimeProbe.cpp off the
	// engine: actor and witness transforms, two line traces and an
	// accumulated watching time. Everything below it is this layer's, and it
	// is what the test runs.
	struct Reading
	{
		std::string WitnessId;
		std::string EventId;      // A or B

		P3     WitnessAt;         // feet, street metres
		P3     EyeAt;             // WitnessAt + kEyeHeightM
		double WitnessYawDeg;
		P3     ActorHeadAt;
		double ActorYawDeg;
		P3     VictimAt;          // the window centre, read off the actor's bounds

		double ActorMetres, ActorOffAxisDeg, ActorTraceLenCm;
		bool   bActorOccluded;
		std::string ActorBlocker;

		double VictimMetres, VictimOffAxisDeg, VictimTraceLenCm;
		bool   bVictimOccluded;
		std::string VictimBlocker;

		double SecondsWatching;
		// THE VANTAGE IS CAPTURED BEFORE THE DEED, WITH THE GLASS STANDING,
		// and the run says so on the line. Once east_parade_glass0 is hidden
		// with its collision off, a trace from the witness's eye to the
		// window centre passes through the empty pane and hits
		// east_parade_interior0 behind it, so victimOccluded would read yes
		// and the accepting case would print as a rejection.
		std::string VantageAt;

		// filled by Resolve
		LedgerCore::Observation O;
		bool        bFiled;
		std::string FiledReason;

		Reading()
			: WitnessYawDeg(0.0), ActorYawDeg(0.0),
			  ActorMetres(0.0), ActorOffAxisDeg(0.0), ActorTraceLenCm(0.0), bActorOccluded(false),
			  ActorBlocker("none"),
			  VictimMetres(0.0), VictimOffAxisDeg(0.0), VictimTraceLenCm(0.0), bVictimOccluded(false),
			  VictimBlocker("none"),
			  SecondsWatching(0.0), VantageAt("before-the-deed/glass-standing"),
			  bFiled(false), FiledReason("nothing-measured")
		{
		}

		bool FaceToward() const
		{
			return FaceAngleDeg(P3(ActorHeadAt.X, ActorHeadAt.Y, ActorHeadAt.Z),
			                    ActorYawDeg, EyeAt) < kFaceArcDegrees;
		}
	};

	inline LedgerCore::Vantage VantageOf(const Reading& R)
	{
		LedgerCore::Vantage V;
		V.WitnessId = R.WitnessId;
		V.ToActor   = LedgerCore::Sight::At(R.ActorMetres, kLightLevel,
		                                    R.ActorOffAxisDeg, R.bActorOccluded);
		V.ToVictim  = LedgerCore::Sight::At(R.VictimMetres, kLightLevel,
		                                    R.VictimOffAxisDeg, R.bVictimOccluded);
		V.Familiarity     = kFamiliarity;
		V.ActorHasMark    = false;
		V.FaceToward      = R.FaceToward();
		V.AmbientFloor    = kAmbientFloor;
		V.Alertness       = (double)kAlertness;
		V.SecondsWatching = R.SecondsWatching;
		V.RungFloor       = kRungFloor;
		V.ArrivedLater    = false;
		return V;
	}

	// WHICH BRANCH WITNESSES.cs RUNS AFTER LINE 207, read out of that file
	// and reproduced here: `var o = Observe.Resolve(deed, v); Last.Add(o); if
	// (!o.Empty) Saw++;`. An empty observation is kept and NOT carried
	// anywhere: nothing is offered to the mill for it, which is why
	// witnessesOffered reads 1 and not 4 on a run where three witnesses saw
	// nothing.
	inline void Resolve(Reading& R, const LedgerCore::Deed& D)
	{
		R.O = LedgerCore::Observe::Resolve(D, VantageOf(R));
		R.bFiled = !R.O.Empty();
		R.FiledReason = R.bFiled ? "none" : "slots-none";
	}

	inline bool HeardAct(const Reading& R, const LedgerCore::Deed& D)
	{
		return D.Loudness > 0
		    && LedgerCore::Perception::Heard(R.VictimMetres, D.Loudness, kAmbientFloor,
		                                     R.bVictimOccluded, (double)kAlertness);
	}

	inline double AudibleRadiusM(const Reading& R, const LedgerCore::Deed& D)
	{
		return LedgerCore::Perception::AudibleRadius(
			D.Loudness,
			LedgerCore::Perception::EffectiveFloor(kAmbientFloor, (double)kAlertness),
			R.bVictimOccluded);
	}

	// THE PER-SAMPLE MOMENT, one line per witness per crime, ruling section 4
	// item 4. Whole-run numbers are never on this line and per-sample numbers
	// are never on a done line.
	inline std::string WitnessLine(const Reading& R, const LedgerCore::Deed& D)
	{
		const LedgerCore::Vantage V = VantageOf(R);
		const bool bLongEnough = R.SecondsWatching >= LedgerCore::Perception::NoticeSeconds;
		const bool bInSightActor = bLongEnough && LedgerCore::Perception::InSight(
			R.ActorMetres, R.ActorOffAxisDeg, kLightLevel, R.bActorOccluded, 1.4);
		const bool bInSightVictim = bLongEnough && LedgerCore::Perception::InSight(
			R.VictimMetres, R.VictimOffAxisDeg, kLightLevel, R.bVictimOccluded, 1.4);
		return "witness=" + NoSpaces(R.WitnessId)
		     + " event=" + NoSpaces(R.EventId)
		     + " witnessAtXYZcm=" + F1(R.WitnessAt.X * 100.0) + "/" + F1(R.WitnessAt.Z * 100.0)
		     + "/" + F1(R.WitnessAt.Y * 100.0)
		     + " witnessYawDeg=" + F1(R.WitnessYawDeg)
		     + " actorMetres=" + F2(R.ActorMetres)
		     + " actorOffAxisDeg=" + F1(R.ActorOffAxisDeg)
		     + " actorOccluded=" + YesNo(R.bActorOccluded)
		     + " actorBlocker=" + NoSpaces(R.ActorBlocker)
		     + " actorTraceLenCm=" + F1(R.ActorTraceLenCm)
		     + " victimMetres=" + F2(R.VictimMetres)
		     + " victimOffAxisDeg=" + F1(R.VictimOffAxisDeg)
		     + " victimOccluded=" + YesNo(R.bVictimOccluded)
		     + " victimBlocker=" + NoSpaces(R.VictimBlocker)
		     + " victimTraceLenCm=" + F1(R.VictimTraceLenCm)
		     + " victimVantageAt=" + NoSpaces(R.VantageAt)
		     + " faceToward=" + YesNo(V.FaceToward)
		     + " faceAngleDeg=" + F1(FaceAngleDeg(R.ActorHeadAt, R.ActorYawDeg, R.EyeAt))
		     + " faceArcDeg=" + F1(kFaceArcDegrees)
		     + " secondsWatching=" + F2(R.SecondsWatching)
		     + " noticeSeconds=" + F2(LedgerCore::Perception::NoticeSeconds)
		     + " inSightActor=" + YesNo(bInSightActor)
		     + " inSightVictim=" + YesNo(bInSightVictim)
		     + " heardAct=" + YesNo(HeardAct(R, D))
		     + " audibleRadiusM=" + F1(AudibleRadiusM(R, D))
		     + " idRung=" + Int(R.O.Rung)
		     + " slots=" + SlotsValue(R.O.Slots)
		     + " label=" + LabelValue(R.O)
		     + " certainty=" + F2(R.O.Certainty)
		     + " filed=" + YesNo(R.bFiled)
		     + " filedReason=" + NoSpaces(R.FiledReason)
		     + " filedBranch=Witnesses.cs-207-210/only-a-non-empty-observation-is-carried";
	}

	// ---- the deed itself, read back off the actor -------------------------
	struct CrimeReading
	{
		std::string Id;           // A or B
		std::string PieceName;
		P3     ActorAt;
		double ActorYawDeg;
		bool   bPieceFound;
		bool   bHiddenBefore, bHiddenAfter, bCollisionAfter;
		int    Shards, ShardsAsked, Bricks, BricksAsked;
		std::string WhyNot;

		CrimeReading()
			: ActorYawDeg(0.0), bPieceFound(false), bHiddenBefore(false), bHiddenAfter(false),
			  bCollisionAfter(true), Shards(0), ShardsAsked(kShardsPerCrime), Bricks(0),
			  BricksAsked(1), WhyNot("none")
		{
		}
	};

	inline std::string CrimeLine(const CrimeReading& C)
	{
		// COMMITTED IS READ BACK OFF THE ACTOR, NEVER OFF THE CALL. A hide
		// that did not take prints NOT-COMMITTED with the flag it read.
		const bool bOk = C.bPieceFound && C.bHiddenAfter && !C.bCollisionAfter;
		return "crime=" + NoSpaces(C.Id)
		     + " piece=" + NoSpaces(C.PieceName)
		     + " pieceFound=" + YesNo(C.bPieceFound)
		     + " actorAtXYZcm=" + F1(C.ActorAt.X * 100.0) + "/" + F1(C.ActorAt.Z * 100.0)
		     + "/" + F1(C.ActorAt.Y * 100.0)
		     + " actorYawDeg=" + F1(C.ActorYawDeg)
		     + " glassHiddenBefore=" + YesNo(C.bHiddenBefore)
		     + " glassHiddenAfter=" + YesNo(C.bHiddenAfter)
		     + " glassCollisionAfter=" + (C.bCollisionAfter ? "on" : "off")
		     + " shards=" + Int(C.Shards) + "/" + Int(C.ShardsAsked)
		     + " brick=" + Int(C.Bricks) + "/" + Int(C.BricksAsked)
		     + " crimeStatus=" + (bOk ? "COMMITTED" : "NOT-COMMITTED")
		     + " crimeNote=" + NoSpaces(C.WhyNot);
	}

	// ---- one gossip round -------------------------------------------------
	struct RoundReading
	{
		int    Round;
		std::string SpeakerId, ListenerId;
		double PairMetres;
		bool   bTogether;
		int    RumoursHeld;
		int    Passed;
		double Tie, HopDecay, MinShare;
		double ConfidenceIn, ConfidencePassed, HeardImportance;
		int    Hops;
		bool   bContradiction, bExposure;
		bool   bRan;

		RoundReading()
			: Round(0), PairMetres(0.0), bTogether(false), RumoursHeld(0), Passed(0),
			  Tie(0.0), HopDecay(0.0), MinShare(0.0), ConfidenceIn(0.0), ConfidencePassed(0.0),
			  HeardImportance(0.0), Hops(0), bContradiction(false), bExposure(false), bRan(false)
		{
		}
	};

	inline std::string GossipRoundLine(const RoundReading& R)
	{
		std::string S = "gossipRound=" + Int(R.Round)
		     + " speaker=" + NoSpaces(R.SpeakerId)
		     + " listener=" + NoSpaces(R.ListenerId)
		     + " pairMetres=" + F1(R.PairMetres)
		     + " talkRangeM=" + F1(kTalkRangeM)
		     + " together=" + YesNo(R.bTogether)
		     + " rumoursHeld=" + Int(R.RumoursHeld)
		     + " passed=" + Int(R.Passed) + "/" + Int(R.RumoursHeld);
		if (!R.bRan)
		{
			return S + " passedStatus=NOTHING-MEASURED";
		}
		if (!R.bTogether)
		{
			return S + " passedStatus=NOT-TOGETHER";
		}
		return S + " tie=" + F2(R.Tie)
		     + " hopDecay=" + F2(R.HopDecay)
		     + " minShare=" + F2(R.MinShare)
		     + " confidenceIn=" + F2(R.ConfidenceIn)
		     + " confidencePassed=" + F2(R.ConfidencePassed)
		     + " hops=" + Int(R.Hops)
		     + " heardMemoryImportance=" + F2(R.HeardImportance)
		     + " contradiction=" + YesNo(R.bContradiction)
		     + " exposure=" + YesNo(R.bExposure)
		     + " passedStatus=" + (R.Passed > 0 ? "PASSED" : "NOT-PASSED");
	}

	// ---- the bank ---------------------------------------------------------
	//
	// A BANK, NOT A C++ LITERAL, ruling section 3: the same text must reach
	// the verdict, the caption and, at the next rung, a voice clip whose
	// filename is a hash of speaker and text, so the text has one home.
	//
	// WHY A SCANNER AND NOT A JSON MODULE. LedgerProbe.Build.cs names Core,
	// CoreUObject, Engine, ImageWrapper and InputCore and nothing else, and
	// every dependency beyond those is time added to every cycle this project
	// exists to measure. This reads the one array it needs, here, where g++
	// runs it against the real bank file before any dispatch.
	inline std::string::size_type SkipWs(const std::string& S, std::string::size_type I)
	{
		while (I < S.size() && (S[I] == ' ' || S[I] == '\t' || S[I] == '\n' || S[I] == '\r')) { ++I; }
		return I;
	}

	// Reads the JSON string starting at the opening quote. Handles the two
	// escapes this bank could carry and passes everything else through; a
	// string that never closes returns false rather than running off the end.
	inline bool ReadJsonString(const std::string& S, std::string::size_type& I, std::string& Out)
	{
		Out.clear();
		if (I >= S.size() || S[I] != '"') { return false; }
		++I;
		while (I < S.size())
		{
			const char C = S[I];
			if (C == '\\')
			{
				if (I + 1 >= S.size()) { return false; }
				const char E = S[I + 1];
				if (E == 'n')      { Out += ' '; }
				else if (E == 't') { Out += ' '; }
				else               { Out += E; }
				I += 2;
				continue;
			}
			if (C == '"') { ++I; return true; }
			Out += C;
			++I;
		}
		return false;
	}

	// One field of one object, by key, within [From, To). Values may be a
	// string or a number; anything else answers false.
	inline bool JsonField(const std::string& S, std::string::size_type From,
	                      std::string::size_type To, const std::string& Key,
	                      std::string& Out)
	{
		const std::string Needle = "\"" + Key + "\"";
		std::string::size_type At = S.find(Needle, From);
		if (At == std::string::npos || At >= To) { return false; }
		At = SkipWs(S, At + Needle.size());
		if (At >= To || S[At] != ':') { return false; }
		At = SkipWs(S, At + 1);
		if (At >= To) { return false; }
		if (S[At] == '"') { return ReadJsonString(S, At, Out); }
		Out.clear();
		while (At < To && S[At] != ',' && S[At] != '}' && S[At] != ' ' && S[At] != '\n')
		{
			Out += S[At];
			++At;
		}
		return !Out.empty();
	}

	// Every top-level object of the bank's `lines` array, as [begin, end)
	// offsets. Brace-counted and string-aware, so a brace inside a line of
	// dialogue cannot split an object.
	inline void BankObjects(const std::string& S,
	                        std::vector<std::pair<std::string::size_type, std::string::size_type> >& Out)
	{
		Out.clear();
		const std::string::size_type Lines = S.find("\"lines\"");
		if (Lines == std::string::npos) { return; }
		std::string::size_type I = S.find('[', Lines);
		if (I == std::string::npos) { return; }
		++I;
		int Depth = 0;
		bool bInString = false;
		std::string::size_type Begin = 0;
		for (; I < S.size(); ++I)
		{
			const char C = S[I];
			if (bInString)
			{
				if (C == '\\') { ++I; continue; }
				if (C == '"')  { bInString = false; }
				continue;
			}
			if (C == '"') { bInString = true; continue; }
			if (C == '{') { if (Depth == 0) { Begin = I; } ++Depth; continue; }
			if (C == '}')
			{
				--Depth;
				if (Depth == 0) { Out.push_back(std::make_pair(Begin, I + 1)); }
				continue;
			}
			if (C == ']' && Depth == 0) { return; }
		}
	}

	// GossipDirector.cs 586: seed = Day * 31 + Hour.
	inline int Seed(const LedgerCore::GameTime& Now) { return Now.Day * 31 + Now.Hour; }

	// THE RULE, NOT THE EXAMPLE. Ruling section 4 item 7 shows
	// cw-ws-r3-02,cw-ov-r3-01, which ONE seed cannot produce: at D1 12:00 the
	// seed is 43 and 43 % 3 is 1 for both contexts, so the second variant is
	// picked in each and the pair is cw-ws-r3-02,cw-ov-r3-02. The seed and
	// the modulus are printed beside the ids so a reader can check the
	// arithmetic rather than take this comment's word.
	inline int VariantIndex(int InSeed, int Variants)
	{
		if (Variants <= 0) { return 0; }
		int I = InSeed % Variants;
		if (I < 0) { I += Variants; }
		return I;
	}

	// Picks the line for this context and rung, at the seed's variant.
	// OutVariants is the modulus and is the COUNT FOUND IN THE BANK, never a
	// typed 3: a bank that grows a fourth variant moves the pick, and a bank
	// missing the cell refuses with the reason rather than picking nothing.
	inline bool BankPick(const std::string& Text, const std::string& Context, int IdRung,
	                     int InSeed, std::string& OutId, std::string& OutText,
	                     std::string& OutSpeaker, int& OutVariants, std::string& OutWhyNot)
	{
		OutId.clear(); OutText.clear(); OutSpeaker.clear();
		OutVariants = 0;
		OutWhyNot = "none";
		std::vector<std::pair<std::string::size_type, std::string::size_type> > Objects;
		BankObjects(Text, Objects);
		if (Objects.empty()) { OutWhyNot = "bank-has-no-lines-array"; return false; }
		std::vector<std::string::size_type> Matching;
		for (std::vector<std::pair<std::string::size_type, std::string::size_type> >::size_type I = 0;
		     I < Objects.size(); ++I)
		{
			std::string Ctx, Rung;
			if (!JsonField(Text, Objects[I].first, Objects[I].second, "context", Ctx)) { continue; }
			if (Ctx != Context) { continue; }
			if (!JsonField(Text, Objects[I].first, Objects[I].second, "idRung", Rung)) { continue; }
			if (std::atoi(Rung.c_str()) != IdRung) { continue; }
			Matching.push_back(I);
		}
		OutVariants = (int)Matching.size();
		if (OutVariants == 0)
		{
			OutWhyNot = "no-line-at-" + NoSpaces(Context) + "-rung-" + Int(IdRung);
			return false;
		}
		const std::string::size_type Pick = Matching[(std::vector<std::string::size_type>::size_type)
			VariantIndex(InSeed, OutVariants)];
		if (!JsonField(Text, Objects[Pick].first, Objects[Pick].second, "id", OutId))
		{
			OutWhyNot = "picked-line-has-no-id";
			return false;
		}
		if (!JsonField(Text, Objects[Pick].first, Objects[Pick].second, "text", OutText))
		{
			OutWhyNot = "picked-line-has-no-text";
			return false;
		}
		JsonField(Text, Objects[Pick].first, Objects[Pick].second, "speaker", OutSpeaker);
		return true;
	}

	// ---- the overheard beat ------------------------------------------------
	struct OverheardReading
	{
		int    Events, EventsAsked;
		double PlayerToW1M, PlayerToN2M;
		int    IdRung;
		int    SeedValue, Variants, VariantPicked;
		std::string SummaryId, ReplyId, BankPath, WhyNot;
		bool   bBankRead;

		OverheardReading()
			: Events(0), EventsAsked(1), PlayerToW1M(0.0), PlayerToN2M(0.0), IdRung(0),
			  SeedValue(0), Variants(0), VariantPicked(0),
			  SummaryId("none"), ReplyId("none"), BankPath("none"), WhyNot("none"),
			  bBankRead(false)
		{
		}

		bool Heard() const
		{
			return Events > 0 && PlayerToW1M <= kEarshotM && PlayerToN2M <= kEarshotM;
		}
	};

	inline std::string OverheardLine(const OverheardReading& O)
	{
		return "overheardEvents=" + Int(O.Events) + "/" + Int(O.EventsAsked)
		     + " overheardPlayerToW1M=" + F1(O.PlayerToW1M)
		     + " overheardPlayerToN2M=" + F1(O.PlayerToN2M)
		     + " earshotM=" + F1(kEarshotM)
		     + " overheardStatus=" + (O.Events <= 0 ? "NOTHING-MEASURED"
		                                            : (O.Heard() ? "HEARD" : "OUT-OF-EARSHOT"))
		     + " overheardSpeakers=w1,n2"
		     + " overheardIdRung=" + Int(O.IdRung)
		     + " overheardLineIds=" + NoSpaces(O.SummaryId) + "," + NoSpaces(O.ReplyId)
		     + " overheardSeed=" + Int(O.SeedValue)
		     + " overheardSeedFormula=Day*31+Hour/GossipDirector.cs-586"
		     + " overheardVariants=" + Int(O.Variants)
		     + " overheardVariantPicked=" + Int(O.VariantPicked)
		     + " overheardBankRead=" + YesNo(O.bBankRead)
		     + " overheardBank=" + NoSpaces(O.BankPath)
		     + " overheardBankNote=" + NoSpaces(O.WhyNot)
		     + " overheardLineSource=bank/StreetVoice.Exchange-not-ported";
	}

	// ---- the sequence keys file --------------------------------------------
	//
	// One line per sequence frame, read by tools/clip-from-frames.py
	// --frame-keys. The caption, the wrapping and every printed number about
	// them live in that tool, where its selftest runs them; this supplies
	// which frame, which beat and which id, and nothing else.
	inline std::string SeqKeyLine(const std::string& FrameName, const std::string& Beat,
	                              const std::string& Speaker, const std::string& LineId,
	                              bool bHeard)
	{
		return "frame=" + NoSpaces(FrameName)
		     + " beat=" + NoSpaces(Beat)
		     + " speaker=" + NoSpaces(Speaker.empty() ? std::string("none") : Speaker)
		     + " lineId=" + NoSpaces(LineId.empty() ? std::string("none") : LineId)
		     + " heard=" + YesNo(bHeard);
	}

	// ---- the three combined readings, rule 5b -------------------------------
	//
	// NO NEW NUMERIC BOUND: every word below is a conjunction of the model's
	// own outputs, and the raw numbers are on the lines above it.
	//
	// witnessStatus needs ALL THREE halves: W1 filed on A with a rung of at
	// least 1, W1 filed nothing on B with actorOccluded, and N2 filed nothing
	// on either. A guard that cannot tell a regression from an improvement is
	// a ratchet, so the case it should PASS and the case it should CATCH both
	// have to have run.
	inline std::string WitnessStatus(const std::vector<Reading>& All)
	{
		if (All.size() < 4) { return "NOTHING-MEASURED"; }
		bool bW1AFiled = false, bW1BRefused = false;
		int  N2Empty = 0, N2Seen = 0;
		for (std::vector<Reading>::size_type I = 0; I < All.size(); ++I)
		{
			const Reading& R = All[I];
			if (R.WitnessId == "w1" && R.EventId == "A") { bW1AFiled = R.bFiled && R.O.Rung >= 1; }
			if (R.WitnessId == "w1" && R.EventId == "B") { bW1BRefused = !R.bFiled && R.bActorOccluded; }
			if (R.WitnessId == "n2") { ++N2Seen; if (!R.bFiled) { ++N2Empty; } }
		}
		if (bW1AFiled && bW1BRefused && N2Seen == 2 && N2Empty == 2) { return "REAL"; }
		return "NOT-PROVEN";
	}

	inline std::string GossipStatus(const RoundReading& One, const RoundReading& Two)
	{
		if (!One.bRan || !Two.bRan) { return "NOTHING-MEASURED"; }
		if (One.Passed == 0 && !One.bTogether && Two.Passed == 1 && Two.bTogether) { return "REAL"; }
		return "NOT-PROVEN";
	}

	// ---- the selftest -------------------------------------------------------
	//
	// ACCEPTING CASE FIRST, then the cases these rules exist to catch. The
	// live decision path is the fixture: every function below is the one the
	// run calls, on the ruling's own numbers.
	struct SelftestResult
	{
		int Checks, Failed;
		std::string FirstFailure;
		SelftestResult() : Checks(0), Failed(0), FirstFailure("none") {}
	};

	inline void Expect(SelftestResult& R, bool bOk, const std::string& What)
	{
		++R.Checks;
		if (!bOk)
		{
			++R.Failed;
			if (R.FirstFailure == "none") { R.FirstFailure = NoSpaces(What); }
		}
	}

	inline SelftestResult Selftest()
	{
		SelftestResult R;

		// 1. THE ACCEPTING CASE: W1 at P1 watching the deed at C_A, on the
		//    ruling's own geometry. Rung 3, four slots, label full,
		//    certainty 0.94, filed.
		Reading A;
		A.WitnessId = "w1"; A.EventId = "A";
		A.WitnessAt = P3(kW1AX, 0.1, kW1AZ);
		A.EyeAt     = P3(kW1AX, 0.1 + kEyeHeightM, kW1AZ);
		A.ActorHeadAt = P3(kCrimeAX, 0.1 + 1.7, kCrimeAZ);
		A.WitnessYawDeg = YawToFace(A.WitnessAt, P3(kCrimeAX, 0.1, kCrimeAZ));
		A.ActorYawDeg = 90.0;
		A.ActorMetres = Metres(P3(kW1AX, 0.0, kW1AZ), P3(kCrimeAX, 0.0, kCrimeAZ));
		A.ActorOffAxisDeg = 0.0;
		A.VictimMetres = Metres(P3(kW1AX, 0.0, kW1AZ), P3(6.869, 0.0, 4.985));
		A.VictimOffAxisDeg = OffAxisDeg(P3(kW1AX, 0.0, kW1AZ), A.WitnessYawDeg,
		                                P3(6.869, 0.0, 4.985));
		A.SecondsWatching = 1.0;
		const LedgerCore::Deed D = MakeDeed("crime_a", "player", "east_parade_glass0");
		Resolve(A, D);
		Expect(R, A.O.Rung == 3, "accepting-case-rung-3");
		Expect(R, SlotsValue(A.O.Slots) == "act,victim,actor,flight", "accepting-case-slots");
		Expect(R, LabelValue(A.O) == "full", "accepting-case-label-full");
		Expect(R, F2(A.O.Certainty) == "0.94", "accepting-case-certainty-0.94");
		Expect(R, A.bFiled, "accepting-case-filed");
		Expect(R, HeardAct(A, D), "accepting-case-heard");
		Expect(R, F1(AudibleRadiusM(A, D)) == "13.1", "accepting-case-audible-radius-13.1");
		Expect(R, F2(A.ActorMetres) == "2.28", "accepting-case-actor-2.28m");
		Expect(R, F2(A.VictimMetres) == "2.15", "accepting-case-victim-2.15m");
		Expect(R, F1(A.VictimOffAxisDeg) == "28.2", "accepting-case-victim-28.2deg");
		Expect(R, F1(FaceAngleDeg(P3(kCrimeAX, 0.1, kCrimeAZ), 90.0,
		                          P3(kW1AX, 0.1, kW1AZ))) == "69.4", "accepting-case-face-69.4deg");
		Expect(R, A.FaceToward(), "accepting-case-face-toward");

		// 2. THE CASE THE PAIR EXISTS TO CATCH: the same witness with the
		//    terrace in the way. Nothing seen, nothing heard, nothing filed.
		Reading B = A;
		B.EventId = "B";
		B.ActorMetres = 20.2; B.VictimMetres = 20.9;
		B.bActorOccluded = true; B.bVictimOccluded = true;
		B.ActorBlocker = "west_south_bay2"; B.VictimBlocker = "west_south_bay2";
		B.SecondsWatching = 0.0;
		Resolve(B, D);
		Expect(R, !B.bFiled, "rejecting-case-not-filed");
		Expect(R, SlotsValue(B.O.Slots) == "none", "rejecting-case-slots-none");
		Expect(R, LabelValue(B.O) == "nothing", "rejecting-case-label-nothing");
		Expect(R, F2(B.O.Certainty) == "0.00", "rejecting-case-certainty-0");
		Expect(R, B.FiledReason == "slots-none", "rejecting-case-reason");
		Expect(R, !HeardAct(B, D), "rejecting-case-not-heard");
		Expect(R, F1(AudibleRadiusM(B, D)) == "1.9", "rejecting-case-occluded-radius");

		// 3. The seed, the modulus and the pick. 43 % 3 == 1 is the whole of
		//    the correction this file carries against section 4's example.
		Expect(R, Seed(LedgerCore::GameTime(1, 12, 0)) == 43, "seed-43-at-D1-12:00");
		Expect(R, VariantIndex(43, 3) == 1, "variant-index-1");
		Expect(R, VariantIndex(43, 0) == 0, "variant-index-refuses-zero-modulus");

		// 4. The bank scanner, on a synthetic bank: the accepting case first,
		//    then a cell that exists nowhere.
		const std::string Fixture =
			"{\"bank\":\"x\",\"lines\":[\n"
			"{\"id\":\"a-1\",\"context\":\"witness_summary\",\"idRung\":3,\"speaker\":\"w1\","
			"\"text\":\"one, with a comma\"},\n"
			"{\"id\":\"a-2\",\"context\":\"witness_summary\",\"idRung\":3,\"speaker\":\"w1\","
			"\"text\":\"two\"},\n"
			"{\"id\":\"a-3\",\"context\":\"witness_summary\",\"idRung\":3,\"speaker\":\"w1\","
			"\"text\":\"three\"},\n"
			"{\"id\":\"b-1\",\"context\":\"overheard\",\"idRung\":1,\"speaker\":\"n2\","
			"\"text\":\"reply\"}]}";
		std::string Id, Txt, Spk, Why;
		int Variants = 0;
		Expect(R, BankPick(Fixture, "witness_summary", 3, 43, Id, Txt, Spk, Variants, Why),
		       "bank-pick-accepts");
		Expect(R, Variants == 3, "bank-pick-counts-three-variants");
		Expect(R, Id == "a-2", "bank-pick-takes-the-seed-s-variant");
		Expect(R, Txt == "one, with a comma" || Id != "a-1", "bank-pick-text-matches-id");
		Expect(R, Spk == "w1", "bank-pick-reads-speaker");
		Expect(R, !BankPick(Fixture, "overheard", 3, 43, Id, Txt, Spk, Variants, Why),
		       "bank-pick-refuses-a-missing-cell");
		Expect(R, Variants == 0, "bank-pick-missing-cell-counts-zero");
		Expect(R, Why == "no-line-at-overheard-rung-3", "bank-pick-names-the-missing-cell");
		Expect(R, !BankPick("{}", "witness_summary", 3, 43, Id, Txt, Spk, Variants, Why),
		       "bank-pick-refuses-a-bankless-file");

		// 5. The value rules every reader of these lines depends on.
		Expect(R, NoSpaces("a b") == "a-b", "no-spaces-in-a-value");
		Expect(R, F2(0.36096) == "0.36", "two-decimals-heard-importance");
		Expect(R, F2(0.125) == "0.13", "two-decimals-is-the-C#-rule-not-printf");
		LedgerCore::Observation Partial;
		Partial.Slots = LedgerCore::Slot::Act | LedgerCore::Slot::Victim;
		Expect(R, LabelValue(Partial) == "act/no-actor", "label-loses-its-space");

		// 6. Every shard sits inside the 1 m the ruling states, on the
		//    footway side of the window foot.
		for (int I = 0; I < ShardOffsetCount(); ++I)
		{
			double DX = 0.0, DZ = 0.0;
			ShardOffset(I, DX, DZ);
			Expect(R, std::sqrt(DX * DX + DZ * DZ) <= 1.0, "shard-" + Int(I) + "-within-1m");
			Expect(R, DZ < 0.0, "shard-" + Int(I) + "-on-the-footway-side");
		}

		// 7. The two combined readings, each on the pair it needs.
		std::vector<Reading> Four;
		Reading N2A = B; N2A.WitnessId = "n2"; N2A.EventId = "A";
		Reading N2B = B; N2B.WitnessId = "n2"; N2B.EventId = "B";
		Four.push_back(A); Four.push_back(B); Four.push_back(N2A); Four.push_back(N2B);
		Expect(R, WitnessStatus(Four) == "REAL", "witnessStatus-accepts-the-real-pair");
		std::vector<Reading> Three(Four.begin(), Four.begin() + 3);
		Expect(R, WitnessStatus(Three) == "NOTHING-MEASURED", "witnessStatus-refuses-a-short-run");
		std::vector<Reading> Broken = Four;
		Broken[1].bFiled = true;   // W1 filed on the crime she could not see
		Expect(R, WitnessStatus(Broken) == "NOT-PROVEN", "witnessStatus-catches-a-filed-blind-witness");
		RoundReading One, Two;
		One.bRan = true; One.bTogether = false; One.Passed = 0;
		Two.bRan = true; Two.bTogether = true;  Two.Passed = 1;
		Expect(R, GossipStatus(One, Two) == "REAL", "gossipStatus-accepts-the-planted-pair");
		RoundReading NeverRan;
		Expect(R, GossipStatus(One, NeverRan) == "NOTHING-MEASURED", "gossipStatus-refuses-a-missing-round");
		Two.Passed = 0;
		Expect(R, GossipStatus(One, Two) == "NOT-PROVEN", "gossipStatus-catches-a-silent-pair");

		return R;
	}
}

namespace LedgerCrimeProbe
{
	// Arms the crime run on the core ticker and returns immediately. The
	// engine quits itself when the last beat is measured or a ceiling bites,
	// and every ceiling that bites is named in the verdict.
	void Start();
}
