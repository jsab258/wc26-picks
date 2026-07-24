using System;

namespace Ledger.Core
{
    public enum TimeSlot { Morning, Afternoon, Evening, Night }

    /// In-game time. Day 1 starts at 06:00; a "day" for scheduling purposes
    /// runs 06:00..05:59. Engine-independent so the sim and tests can run headless.
    public struct GameTime : IComparable<GameTime>, IEquatable<GameTime>
    {
        public int Day;
        public int Hour;
        public int Minute;

        public GameTime(int day, int hour, int minute)
        {
            Day = day;
            Hour = hour;
            Minute = minute;
        }

        public long TotalMinutes => ((long)Day * 24 + Hour) * 60 + Minute;

        public static GameTime FromTotalMinutes(long total)
        {
            long day = total / (24 * 60);
            long rem = total % (24 * 60);
            return new GameTime((int)day, (int)(rem / 60), (int)(rem % 60));
        }

        public GameTime AddMinutes(int minutes) => FromTotalMinutes(TotalMinutes + minutes);

        public double HoursUntil(GameTime later) => (later.TotalMinutes - TotalMinutes) / 60.0;

        public TimeSlot Slot
        {
            get
            {
                if (Hour >= 6 && Hour < 12) return TimeSlot.Morning;
                if (Hour >= 12 && Hour < 18) return TimeSlot.Afternoon;
                if (Hour >= 18 && Hour < 23) return TimeSlot.Evening;
                return TimeSlot.Night;
            }
        }

        public int CompareTo(GameTime other) => TotalMinutes.CompareTo(other.TotalMinutes);
        public bool Equals(GameTime other) => TotalMinutes == other.TotalMinutes;
        public override bool Equals(object obj) => obj is GameTime other && Equals(other);
        public override int GetHashCode() => TotalMinutes.GetHashCode();

        public override string ToString() => $"D{Day} {Hour:D2}:{Minute:D2}";

        /// Parses the "D3 14:05" format produced by ToString.
        public static bool TryParse(string s, out GameTime time)
        {
            time = default;
            if (string.IsNullOrWhiteSpace(s) || s[0] != 'D') return false;
            var parts = s.Substring(1).Split(new[] { ' ', ':' }, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length != 3) return false;
            if (!int.TryParse(parts[0], out var d) || !int.TryParse(parts[1], out var h) || !int.TryParse(parts[2], out var m))
                return false;
            time = new GameTime(d, h, m);
            return true;
        }
    }
}
