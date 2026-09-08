// TRANSLITERATION of ledger/Assets/Scripts/Core/GameTime.cs, D1 probe.
//
// TRANSLITERATION, NOT REWRITE, and the distinction is the whole method: the
// C# suite is the behavioural definition, so every constant and every branch
// here matches its source line for line, and where the C# is subtle the
// comment explaining why travels with it. A port that "improved" something
// would make the two engines incomparable, which is the one thing D1 must
// not allow.
//
// SCOPE, from the crime ruling section 1 item 3: GameTime.cs 9 to 22 and 51.
// Day, Hour, Minute, the constructor, TotalMinutes and ToString. NO PARSING
// AND NO SLOTS: TimeSlot, FromTotalMinutes, AddMinutes, HoursUntil, Slot,
// CompareTo, Equals, GetHashCode and TryParse are not ported, because
// nothing the crime run does reads them and a member ported without a caller
// is a member nobody checks.
//
// NO UNREAL TYPE IS IN THIS FILE, deliberately, and it is the standing rule
// from 25 August rather than a preference: measurement arithmetic and
// formatting live where the tests run. This project's top layer does not
// compile in the container that writes it, so a formatter written there
// ships UNRUN and an unrun formatter printing a plausible string is the
// quietest instrument fault there is. ue-probe/tests/core-port-test.cpp
// compiles this with g++ and checks every line of it against a table the
// REAL C# emitted.
#pragma once

#include <cstdio>
#include <string>

namespace LedgerCore
{
	// GameTime.cs 9 to 22. In-game time. Day 1 starts at 06:00; a "day" for
	// scheduling purposes runs 06:00..05:59. Engine-independent so the sim
	// and the tests can run headless, which is exactly why it ports at all.
	struct GameTime
	{
		int Day;
		int Hour;
		int Minute;

		GameTime() : Day(0), Hour(0), Minute(0) {}
		GameTime(int InDay, int InHour, int InMinute)
			: Day(InDay), Hour(InHour), Minute(InMinute) {}

		// GameTime.cs 22. long, not int, in the C# and long long here: the
		// product is days times 1440 and a campaign is allowed to be long.
		long long TotalMinutes() const
		{
			return ((long long)Day * 24 + Hour) * 60 + Minute;
		}

		// GameTime.cs 51: $"D{Day} {Hour:D2}:{Minute:D2}".
		//
		// THE ONE DIFFERENCE BETWEEN D2 AND %02d IS THE SIGN, and it is named
		// rather than left to be discovered: C# renders (-5).ToString("D2") as
		// "-05" and printf renders %02d as "-5". No negative hour or minute
		// can reach here (the only producer is a GameTime built by the probe
		// from a clock), so the two agree on every value this port sees, and
		// the golden table holds a row for the zero and the two-digit case.
		std::string ToString() const
		{
			char Buf[64];
			std::snprintf(Buf, sizeof(Buf), "D%d %02d:%02d", Day, Hour, Minute);
			return std::string(Buf);
		}
	};
}
