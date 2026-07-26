using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// The honest life's missing half (design-doc §6.6): a day job. V1 is the
    /// courier track — morning shifts at Meridian Parcel, accepted at the
    /// dispatch board, walked waypoint to waypoint, paid in clean money. The
    /// job is cover: a person with a route and a timecard reads honest, and
    /// the day circle's suspicion breathes out a little. Time is the resource
    /// (P1): a morning spent carrying parcels is a morning not spent on the
    /// other ledger. Pure state; the world wires the places.
    public class DayJob
    {
        public int PayPerShift = 40;
        public const int AcceptFromHour = 8;
        public const int AcceptUntilHour = 12; // the board comes down at noon
        public const int LapseHour = 18;       // parcels are due by evening

        public bool ShiftActive { get; private set; }
        public int WaypointIndex { get; private set; }
        public int ShiftsWorked { get; private set; }
        public int LastShiftDay { get; private set; } = -1;
        public int LastWorkedDay { get; private set; } = -1;

        /// One shift a day, mornings only, never mid-shift.
        public bool CanAccept(GameTime now) =>
            !ShiftActive && LastShiftDay != now.Day
            && now.Hour >= AcceptFromHour && now.Hour < AcceptUntilHour;

        public bool Accept(GameTime now)
        {
            if (!CanAccept(now)) return false;
            ShiftActive = true;
            WaypointIndex = 0;
            LastShiftDay = now.Day;
            return true;
        }

        /// The player reached the current stop. Returns true when that stop
        /// was the last one; callers then complete the shift.
        public bool Advance(int waypointCount)
        {
            if (!ShiftActive) return false;
            WaypointIndex++;
            return WaypointIndex >= waypointCount;
        }

        /// The round is walked: clean pay, and the day remembers you worked.
        public int Complete(Wallet wallet, GameTime now)
        {
            if (!ShiftActive) return 0;
            ShiftActive = false;
            ShiftsWorked++;
            LastWorkedDay = now.Day;
            wallet.EarnClean(PayPerShift);
            return PayPerShift;
        }

        /// Evening arrived with parcels undelivered — no pay, and the board
        /// remembers who didn't finish (a soft cost only, per the no-timers
        /// rule: nothing expires, the day just ends).
        public bool Lapse(GameTime now)
        {
            if (!ShiftActive || (now.Hour >= AcceptFromHour && now.Hour < LapseHour)) return false;
            ShiftActive = false;
            return true;
        }

        /// Cover: did honest work happen yesterday? The morning close asks.
        public bool WorkedYesterday(GameTime now) => LastWorkedDay == now.Day - 1;

        public Dictionary<string, object> Capture() => new Dictionary<string, object>
        {
            { "shiftActive", ShiftActive }, { "waypoint", WaypointIndex },
            { "worked", ShiftsWorked }, { "lastShiftDay", LastShiftDay },
            { "lastWorkedDay", LastWorkedDay },
        };

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            ShiftActive = data.TryGetValue("shiftActive", out var sa) && sa is bool b && b;
            WaypointIndex = MiniJson.GetInt(data, "waypoint");
            ShiftsWorked = MiniJson.GetInt(data, "worked");
            LastShiftDay = data.ContainsKey("lastShiftDay") ? MiniJson.GetInt(data, "lastShiftDay") : -1;
            LastWorkedDay = data.ContainsKey("lastWorkedDay") ? MiniJson.GetInt(data, "lastWorkedDay") : -1;
        }
    }
}
