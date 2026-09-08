// TRANSLITERATION of ledger/Assets/Scripts/Core/Suspicion.cs, D1 probe.
//
// TRANSLITERATION, NOT REWRITE, and the distinction is the whole method: the
// C# suite is the behavioural definition, so every constant and every branch
// here matches its source line for line, and where the C# is subtle the
// comment explaining why travels with it. A port that "improved" something
// would make the two engines incomparable, which is the one thing D1 must
// not allow.
//
// SCOPE, from the crime ruling section 1 item 5: Fact 10 to 43 with its null
// refusals, ClaimResult 45, KnowledgeBase 49 to 66. Eighteen lines that let
// Gossip.cs Witness 290 and Tick 400 stay verbatim.
//
// SuspicionTracker IS NOT PORTED. It is named out of scope by the ruling,
// which means the two Suspicion.Raise calls inside GossipMill.Tick are
// absent; Gossip.h names that omission at each of the two sites, and the
// crime verdict prints
// gossipSuspicionPorted=no/SuspicionTracker-out-of-scope.
//
// NO UNREAL TYPE IS IN THIS FILE, deliberately: the standing rule from 25
// August is that the arithmetic and the strings live where the tests run,
// because this project's top layer does not compile in the container that
// writes it.
#pragma once

#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

// EXCEPTIONS ARE A FACT ABOUT THE BUILD, NOT ABOUT THE MODEL, and this
// project's top layer is a module that does not enable them. Nothing else
// under ue-probe/Source uses try, catch or throw; g++ in the container has
// them on. Whether Unreal's MSVC configuration accepts a throw in a module
// that disables exceptions is a fact about Jafar's PC that cannot be read
// from here, so it is PRE-RULED (director, 2026-09-08, section 6 item 2): if
// the build refuses, LedgerProbe.Build.cs adds one line,
//
//     PublicDefinitions.Add("LEDGER_CORE_NO_EXCEPTIONS=1");
//
// the four FactNull rows count as Unknown, and the verdict says why. NOT
// bEnableExceptions = true: that changes every translation unit's flags for
// the sake of a test path and moves the build number D1 exists to measure.
// The container keeps proving the four rows either way.
#if defined(LEDGER_CORE_NO_EXCEPTIONS)
	#define LEDGER_CORE_EXCEPTIONS 0
#else
	#define LEDGER_CORE_EXCEPTIONS 1
	#include <stdexcept>
#endif

namespace LedgerCore
{
	// THE REFUSAL WITHOUT EXCEPTIONS, and it is still a refusal. The C#
	// comment below insists the refusal be loud and say which argument;
	// lowering a null to an empty string is the one thing it forbids, and a
	// module with no exceptions still has a way to stop. Unreachable in the
	// crime run, which builds every Fact from std::string.
	inline void RefuseNullArgument(const char* Which)
	{
		std::fprintf(stderr, "LedgerCore::Fact refused a null argument: %s\n", Which);
		std::abort();
	}

	// C#'s ToLowerInvariant over ASCII. The ids and predicates this probe
	// builds are ASCII by construction; the difference from the C# is that
	// the C# would also fold non-ASCII letters, and it is named here rather
	// than assumed away.
	inline std::string ToLowerInvariantAscii(const std::string& S)
	{
		std::string Out = S;
		for (std::string::size_type I = 0; I < Out.size(); ++I)
		{
			Out[I] = (char)std::tolower((unsigned char)Out[I]);
		}
		return Out;
	}

	// Suspicion.cs 10 to 43. A structured fact an NPC holds:
	// ("player", "location_d2_evening", "warehouse"). Facts power the
	// contradiction check that moves suspicion: the game state decides
	// whether a lie lands, the model only performs the reaction.
	class Fact
	{
	public:
		std::string Subject;
		std::string Predicate;
		std::string Value;

		// NULL IS NAMED RATHER THAN DEREFERENCED, and it is not hygiene.
		//
		// SaveChaos found this from the other end: a save file whose rumour
		// record had lost its subj key handed a null straight into
		// ToLowerInvariant(), and the NullReferenceException went all the way
		// out through SaveCodec.Restore, which the front end catches
		// SaveIncompatibleException from and nothing else. A player with a
		// half-written save got a stack trace on the load screen.
		//
		// NOT MADE PERMISSIVE. Defaulting null to "" would have silenced the
		// crash and built a fact with an empty subject, and SameTopic
		// compares subject and predicate, so every gutted fact would match
		// every other gutted fact and contradict them. A quiet wrong answer
		// in the one system the game uses to decide whether a lie lands is
		// worse than a loud refusal, so the refusal is loud and says which
		// argument.
		//
		// WHAT NULL IS IN C++. A std::string cannot be null, so the refusal
		// would have vanished in translation and taken the behaviour with
		// it. The pointer overload is therefore the primary constructor and
		// it is the one the refusal lives in; the std::string overload
		// forwards to it and can never trip it. C#'s ArgumentNullException
		// becomes std::invalid_argument carrying the SAME argument name,
		// because "which argument" is the part of the refusal that was worth
		// having.
		Fact(const char* InSubject, const char* InPredicate, const char* InValue)
		{
#if LEDGER_CORE_EXCEPTIONS
			if (InSubject == 0)   { throw std::invalid_argument("subject"); }
			if (InPredicate == 0) { throw std::invalid_argument("predicate"); }
			if (InValue == 0)     { throw std::invalid_argument("value"); }
#else
			if (InSubject == 0)   { RefuseNullArgument("subject"); }
			if (InPredicate == 0) { RefuseNullArgument("predicate"); }
			if (InValue == 0)     { RefuseNullArgument("value"); }
#endif
			Subject   = ToLowerInvariantAscii(InSubject);
			Predicate = ToLowerInvariantAscii(InPredicate);
			Value     = ToLowerInvariantAscii(InValue);
		}

		Fact(const std::string& InSubject, const std::string& InPredicate,
		     const std::string& InValue)
			: Subject(ToLowerInvariantAscii(InSubject)),
			  Predicate(ToLowerInvariantAscii(InPredicate)),
			  Value(ToLowerInvariantAscii(InValue))
		{
		}

		// Suspicion.cs 41.
		bool SameTopic(const Fact& Other) const
		{
			return Subject == Other.Subject && Predicate == Other.Predicate;
		}

		// Suspicion.cs 42.
		std::string ToString() const { return Subject + "." + Predicate + "=" + Value; }
	};

	// Suspicion.cs 45. enum class rather than a plain enum so the three C#
	// names survive intact: Unknown and Consistent are common enough words
	// that an unscoped enum would have forced a rename, and a renamed value
	// is one more thing a reader has to hold while comparing two engines.
	enum class ClaimResult { Unknown, Consistent, Contradiction };

	// Suspicion.cs 49 to 66. What one NPC actually knows (witnessed or
	// heard). Claims by the player are checked against this: an NPC cannot be
	// talked out of what it knows.
	class KnowledgeBase
	{
	public:
		std::vector<Fact> Facts;

		// Suspicion.cs 53 to 58.
		void Learn(const Fact& InFact)
		{
			// Later information about the same topic replaces earlier (people
			// update). C#'s RemoveAll over the list, in place, then Add.
			std::vector<Fact> Kept;
			Kept.reserve(Facts.size());
			for (std::vector<Fact>::size_type I = 0; I < Facts.size(); ++I)
			{
				if (!Facts[I].SameTopic(InFact)) { Kept.push_back(Facts[I]); }
			}
			Facts.swap(Kept);
			Facts.push_back(InFact);
		}

		// Suspicion.cs 60 to 65. FirstOrDefault: the FIRST fact on the topic,
		// not the best or the last, and Learn is what keeps there being only
		// one.
		ClaimResult CheckClaim(const Fact& Claim) const
		{
			for (std::vector<Fact>::size_type I = 0; I < Facts.size(); ++I)
			{
				if (Facts[I].SameTopic(Claim))
				{
					return Facts[I].Value == Claim.Value
					     ? ClaimResult::Consistent : ClaimResult::Contradiction;
				}
			}
			return ClaimResult::Unknown;
		}
	};
}
