// TRANSLITERATION of ledger/Assets/Scripts/Core/MemoryStore.cs, D1 probe.
//
// TRANSLITERATION, NOT REWRITE, and the distinction is the whole method: the
// C# suite is the behavioural definition, so every constant and every branch
// here matches its source line for line, and where the C# is subtle the
// comment explaining why travels with it. A port that "improved" something
// would make the two engines incomparable, which is the one thing D1 must
// not allow.
//
// SCOPE, from the crime ruling section 1 item 4: MemoryEvent 8 to 24;
// MemoryStore 55 to 99 IN MEMORY ONLY (MaxEvents, PruneTo, Append, Prune),
// EventsOnDay 124 to 125, ToMarkdown 148 to 159. The markdown IS the
// artefact of "permanently remember" and the crime run commits it.
//
// _filePath IS ALWAYS NULL HERE, which is the C#'s own in-memory mode, so
// LoadFrom, Save, AppendToFile, MemoryEvent.FromLine and ReplaceBeliefs are
// not ported. Each site where the C# would have touched a file says so
// below rather than leaving a reader to wonder which lines went missing.
//
// NO UNREAL TYPE IS IN THIS FILE, deliberately, and it is the standing rule
// from 25 August rather than a preference: measurement arithmetic and
// formatting live where the tests run, because a formatter written in this
// project's top layer ships UNRUN and an unrun formatter printing a
// plausible string is the quietest instrument fault there is.
#pragma once

#include "GameTime.h"
#include "Perception.h"   // LedgerCore::Clamp

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace LedgerCore
{
	// C# Trim() over ASCII. C#'s Trim removes Unicode whitespace and this
	// removes the six ASCII ones; every string this probe builds is ASCII by
	// construction (ids, bank lines, the summaries in Gossip.cs), so the two
	// agree on everything in the crime run, and the difference is named here
	// rather than assumed away.
	inline std::string TrimAscii(const std::string& S)
	{
		const char* Ws = " \t\n\v\f\r";
		const std::string::size_type A = S.find_first_not_of(Ws);
		if (A == std::string::npos) { return std::string(); }
		const std::string::size_type B = S.find_last_not_of(Ws);
		return S.substr(A, B - A + 1);
	}

	// C# string.Replace(old, new): EVERY occurrence, not the first.
	inline std::string ReplaceAll(const std::string& S, const std::string& From,
	                              const std::string& To)
	{
		if (From.empty()) { return S; }
		std::string Out;
		std::string::size_type P = 0;
		for (;;)
		{
			const std::string::size_type At = S.find(From, P);
			if (At == std::string::npos) { Out.append(S, P, S.size() - P); return Out; }
			Out.append(S, P, At - P);
			Out += To;
			P = At + From.size();
		}
	}

	// THE SHORTEST DECIMAL THAT READS BACK AS THIS DOUBLE, which is what
	// .NET's "R" and .NET Core 3.0's default double formatting produce. Used
	// by the golden table to write a double, and NOT by FormatTwoDecimals:
	// see the measurement below.
	inline std::string ShortestRoundTrip(double V)
	{
		char Buf[64];
		for (int Prec = 1; Prec <= 17; ++Prec)
		{
			std::snprintf(Buf, sizeof(Buf), "%.*g", Prec, V);
			if (std::strtod(Buf, 0) == V) { return std::string(Buf); }
		}
		return std::string(Buf);
	}

	// Increment a string of decimal digits by one, carrying leftwards.
	inline std::string IncrementDigits(const std::string& In)
	{
		std::string D = In;
		for (int I = (int)D.size() - 1; I >= 0; --I)
		{
			if (D[I] != '9') { D[I] = (char)(D[I] + 1); return D; }
			D[I] = '0';
		}
		return "1" + D;
	}

	// FIFTEEN SIGNIFICANT DIGITS, which is where .NET starts a custom format
	// string. Not the shortest round-trip: the two differ and the difference
	// is measured below.
	inline std::string FifteenSignificantDigits(double V)
	{
		char Buf[64];
		std::snprintf(Buf, sizeof(Buf), "%.15g", V);
		return std::string(Buf);
	}

	// C#'s Importance.ToString("0.00", InvariantCulture), AND IT IS NEITHER
	// printf("%.2f") NOR A ROUNDING OF THE SHORTEST ROUND-TRIP. Two
	// measurements, both taken in this container against .NET 8 and glibc,
	// and the second one exists because the first was set from a series that
	// did not contain the case the rule is about (rule 2).
	//
	// MEASUREMENT ONE, six values, C# "0.00" against C printf %.2f:
	//
	//     value    C# "0.00"    C printf %.2f
	//     0.125      0.13           0.12
	//     0.015      0.02           0.01
	//     0.045      0.05           0.04
	//     0.345      0.35           0.34
	//     0.135      0.14           0.14
	//     0.005      0.01           0.01
	//
	// printf rounds the exact BINARY value half to even, so 0.125 (exactly
	// representable) goes down to 0.12. C# rounds a DECIMAL digit buffer half
	// away from zero, so it goes up to 0.13. A port using %.2f would have
	// written a different importance into the memory markdown the crime run
	// COMMITS, for every value on a binary-exact or below-half boundary, and
	// the difference would have been invisible until somebody diffed two
	// engines' memory files by eye.
	//
	// MEASUREMENT TWO, ordered by the director's ruling of 2026-09-08 because
	// the first left the rule underdetermined. Which decimal buffer? .NET's
	// Number.Formatting.cs sets DoublePrecisionCustomFormat = 15, so a custom
	// format renders FIFTEEN SIGNIFICANT DIGITS first; the alternative reading
	// was the shortest decimal that round-trips. Both agree on every value in
	// measurement one, the longest of which is five digits. They part one ulp
	// below a half, which is exactly what a product of three factors makes.
	// Measured, C# on the two neighbour doubles:
	//
	//     Math.BitDecrement(0.125) = 0.12499999999999999 -> "0.00" gives 0.13
	//     Math.BitDecrement(0.135) = 0.13499999999999998 -> "0.00" gives 0.14
	//
	// So the fifteen-digit reading is the right one and the shortest
	// round-trip reading is wrong: it would have rendered 0.12499999999999999
	// and printed 0.12. glibc's %.15g gives 0.125 and 0.135 for those two
	// doubles, which is the same buffer .NET builds, and the golden table
	// carries both rows so the rule is a thing the table checked rather than
	// a thing this comment claims.
	inline std::string FormatTwoDecimals(double V)
	{
		const bool bNeg = V < 0.0;
		const std::string S = FifteenSignificantDigits(bNeg ? -V : V);

		// value = Digits * 10^(Exp - FracLen)
		std::string Mant = S;
		int Exp = 0;
		const std::string::size_type EAt = S.find_first_of("eE");
		if (EAt != std::string::npos)
		{
			Mant = S.substr(0, EAt);
			Exp = std::atoi(S.c_str() + EAt + 1);
		}
		int FracLen = 0;
		std::string Digits;
		const std::string::size_type Dot = Mant.find('.');
		if (Dot == std::string::npos) { Digits = Mant; }
		else
		{
			Digits = Mant.substr(0, Dot) + Mant.substr(Dot + 1);
			FracLen = (int)(Mant.size() - Dot - 1);
		}
		if (Digits.empty()) { Digits = "0"; }

		// Shift so the last kept digit is the hundredths place.
		const int Shift = (Exp - FracLen) + 2;
		std::string Kept;
		if (Shift >= 0)
		{
			Kept = Digits;
			Kept.append((std::string::size_type)Shift, '0');
		}
		else
		{
			const int Drop = -Shift;
			char FirstDropped = '0';
			if (Drop >= (int)Digits.size())
			{
				if (Drop == (int)Digits.size()) { FirstDropped = Digits[0]; }
				Kept = "0";
			}
			else
			{
				FirstDropped = Digits[Digits.size() - (std::string::size_type)Drop];
				Kept = Digits.substr(0, Digits.size() - (std::string::size_type)Drop);
			}
			// HALF AWAY FROM ZERO, on the fifteen-digit decimal buffer, which
			// is the rule both measurements above support. Half to even here
			// would print 0.12 for 0.125.
			if (FirstDropped >= '5') { Kept = IncrementDigits(Kept); }
		}

		while (Kept.size() < 3) { Kept = "0" + Kept; }
		std::string Whole = Kept.substr(0, Kept.size() - 2);
		// Strip the leading zeros C# would not print, but keep one digit.
		std::string::size_type NZ = Whole.find_first_not_of('0');
		Whole = (NZ == std::string::npos) ? std::string("0") : Whole.substr(NZ);
		return (bNeg ? "-" : "") + Whole + "." + Kept.substr(Kept.size() - 2);
	}

	// MemoryStore.cs 8 to 24.
	class MemoryEvent
	{
	public:
		GameTime    Time;
		std::string Kind;        // conversation | observation | heard | reflection
		double      Importance;  // 0..1
		std::string Text;

		MemoryEvent(const GameTime& InTime, const std::string& InKind,
		            double InImportance, const std::string& InText)
			: Time(InTime), Kind(InKind),
			  Importance(Clamp(InImportance, 0.0, 1.0)),
			  Text(TrimAscii(ReplaceAll(InText, "\n", " ")))
		{
		}

		// MemoryStore.cs 22 to 23.
		std::string ToLine() const
		{
			return "- [" + Time.ToString() + "] (" + FormatTwoDecimals(Importance)
			     + "|" + Kind + ") " + Text;
		}
	};

	// MemoryStore.cs 55 to 99, 124 to 125, 148 to 159. One character's
	// persistent memory: an append-only event stream plus a small set of
	// distilled beliefs. Stored as human-readable markdown so memories can be
	// inspected, debugged and hand-edited.
	class MemoryStore
	{
	public:
		// MemoryStore.cs 62 to 63. A long campaign must not grow a brain
		// without bound (audit 2026-07-27): past this cap the weakest events
		// from the OLDER half give way in blocks, so the day that mattered
		// survives a thousand ordinary hours. Generous on purpose: pruning is
		// for scale, not for forgetting.
		static const int MaxEvents = 600;
		static const int PruneTo   = 500;

		std::string CharacterId;

		// THE BELIEFS LIST IS PORTED AND IS ALWAYS EMPTY, and saying so is
		// the point. ToMarkdown writes a "## Beliefs" section whether or not
		// anything fills it, so dropping the field would have changed the
		// committed artefact. Nothing in scope can fill it: ReplaceBeliefs
		// (113 to 122) and LoadFrom (127 to 146) are the only two writers in
		// the C# and neither is ported.
		std::vector<std::string> Beliefs;
		std::vector<MemoryEvent> Events;

		explicit MemoryStore(const std::string& InCharacterId)
			: CharacterId(InCharacterId)
		{
			// MemoryStore.cs 73 to 78: the constructor's second argument is
			// the file path and it is null here by the ruling, so the
			// LoadFrom(File.ReadAllText(...)) branch cannot be taken and is
			// not ported.
		}

		// MemoryStore.cs 80 to 88.
		void Append(const MemoryEvent& E)
		{
			Events.push_back(E);
			if ((int)Events.size() > MaxEvents)
			{
				Prune();
				// C# calls Save() here (structure changed: full rewrite).
				// _filePath is null, so Save returns immediately; not ported.
			}
			// C# else-branch: if (!AppendToFile(e)) Save(). For an in-memory
			// store AppendToFile returns true at its first line, so nothing
			// happens; not ported.
		}

		// MemoryStore.cs 92 to 99. Drop the lowest-importance events from the
		// older half until the list is back to PruneTo. Recency shields the
		// newer half entirely.
		//
		// BY INDEX, BECAUSE THE C# SET IS A SET OF REFERENCES. The C# builds
		// a HashSet<MemoryEvent> of the doomed OBJECTS and removes exactly
		// those instances; two events that happen to be equal field for field
		// are still two objects there. A C++ vector of values has no such
		// identity, so the port marks the chosen indices instead, which is
		// the same removal for every input and does not accidentally delete a
		// duplicate the C# would have kept.
		//
		// TIES ARE ENGINE-DEFINED AND THE GOLDEN CASE AVOIDS THEM. C#'s
		// List.Sort is an unstable introsort and so is std::sort, so two
		// events of EQUAL importance in the old half may be dropped in either
		// order by either engine. std::stable_sort here makes this side
		// deterministic; the scenario in the golden table uses distinct
		// importances so the comparison is well defined rather than lucky.
		void Prune()
		{
			const int Half = (int)Events.size() / 2;
			std::vector<int> OldHalf;
			OldHalf.reserve((std::vector<int>::size_type)Half);
			for (int I = 0; I < Half; ++I) { OldHalf.push_back(I); }
			std::stable_sort(OldHalf.begin(), OldHalf.end(), ByImportance(*this));
			const int ToDrop = (int)Events.size() - PruneTo;
			const int N = ToDrop < (int)OldHalf.size() ? ToDrop : (int)OldHalf.size();

			std::vector<bool> Doomed(Events.size(), false);
			for (int I = 0; I < N; ++I) { Doomed[(std::vector<bool>::size_type)OldHalf[(std::vector<int>::size_type)I]] = true; }
			std::vector<MemoryEvent> Kept;
			Kept.reserve(Events.size());
			for (std::vector<MemoryEvent>::size_type I = 0; I < Events.size(); ++I)
			{
				if (!Doomed[I]) { Kept.push_back(Events[I]); }
			}
			Events.swap(Kept);
		}

		// MemoryStore.cs 124 to 125.
		std::vector<MemoryEvent> EventsOnDay(int Day) const
		{
			std::vector<MemoryEvent> Out;
			for (std::vector<MemoryEvent>::size_type I = 0; I < Events.size(); ++I)
			{
				if (Events[I].Time.Day == Day) { Out.push_back(Events[I]); }
			}
			return Out;
		}

		// MemoryStore.cs 148 to 159. AppendLine is "\n" here: the C# uses
		// StringBuilder.AppendLine, whose separator is Environment.NewLine
		// and is therefore "\r\n" on Jafar's Windows PC and "\n" on the Linux
		// container. THE PORT WRITES "\n" ALWAYS and the golden comparison
		// normalises, because a line ending is a platform fact and not a
		// behaviour of the memory model; the committed artefact is compared
		// line by line, never byte by byte.
		std::string ToMarkdown() const
		{
			std::string Sb;
			Sb += "# Memory: " + CharacterId + "\n";
			Sb += "\n";
			Sb += "## Beliefs\n";
			for (std::vector<std::string>::size_type I = 0; I < Beliefs.size(); ++I)
			{
				Sb += "- " + Beliefs[I] + "\n";
			}
			Sb += "\n";
			Sb += "## Events\n";
			for (std::vector<MemoryEvent>::size_type I = 0; I < Events.size(); ++I)
			{
				Sb += Events[I].ToLine() + "\n";
			}
			return Sb;
		}

	private:
		// A comparator object rather than a lambda, because this file
		// compiles under -std=c++11 in the container and inside Unreal's own
		// toolchain, and the plainest construct is the one that survives
		// both.
		struct ByImportance
		{
			const MemoryStore& S;
			explicit ByImportance(const MemoryStore& InS) : S(InS) {}
			bool operator()(int A, int B) const
			{
				return S.Events[(std::vector<MemoryEvent>::size_type)A].Importance
				     < S.Events[(std::vector<MemoryEvent>::size_type)B].Importance;
			}
		};
	};
}
