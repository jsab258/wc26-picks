using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    public enum BeatState { Pending, Attended, Skipped }

    /// An authored social obligation: someone from the day life asks for the
    /// player's evening — deliberately overlapping the outfit's drop window, so the
    /// two lives compete for the same hours (design-doc §4, "obligations compete
    /// for slots"). Not a hard timer: attending is presence during the window, the
    /// windows overlap enough that a determined player can thread both, and
    /// skipping costs standing with a person — never the game.
    public class Beat
    {
        public string Id;
        public string HostId;        // who is asking
        public string Title;         // "Tea with Ada"
        public string InviteText;    // the morning ask, in the host's voice
        public int Day;              // campaign day it happens
        public int StartHour;        // window start (may overlap the drop window)
        public int EndHour;          // exclusive; 24 = midnight
        public BeatState State { get; private set; } = BeatState.Pending;

        public double LoyaltyGain = 0.2;
        public double SuspicionRelief = 0.1;
        public double LoyaltyCostSkip = 0.15;

        public bool InWindow(GameTime t) => t.Day == Day && t.Hour >= StartHour && t.Hour < EndHour;
        public bool WindowPassed(GameTime t) => t.Day > Day || (t.Day == Day && t.Hour >= EndHour);

        /// Save-load overlay.
        public void Restore(BeatState state) => State = state;

        /// The player showed up. Time spent is the maintenance the double life
        /// steals (design-doc §6.4): loyalty up, suspicion eased, a warm memory.
        public void Attend(Gossiper host, GameTime now)
        {
            if (State != BeatState.Pending || host == null) return;
            State = BeatState.Attended;
            host.Loyalty = Math.Clamp(host.Loyalty + LoyaltyGain, 0, 1);
            host.Suspicion.Lower(SuspicionRelief, $"the new owner made time for {Title.ToLowerInvariant()}");
            host.Memory.Append(new MemoryEvent(now, "conversation", 0.7,
                $"The new owner actually came. {Title} — and they stayed. That counts for something."));
        }

        /// The window closed without them. People remember being stood up.
        public void Skip(Gossiper host, GameTime now)
        {
            if (State != BeatState.Pending || host == null) return;
            State = BeatState.Skipped;
            host.Loyalty = Math.Clamp(host.Loyalty - LoyaltyCostSkip, 0, 1);
            host.Memory.Append(new MemoryEvent(now, "observation", 0.65,
                $"I asked the new owner to come. {Title}. They never showed. Noted."));
        }
    }

    /// The week's authored beats, campaign-day keyed. Resolution is pulled by the
    /// game clock: on each tick, anything whose window has passed unattended is
    /// skipped exactly once.
    public class BeatBook
    {
        readonly List<Beat> _beats = new List<Beat>();

        public void Add(Beat b) => _beats.Add(b);
        public IEnumerable<Beat> All => _beats;

        /// The beat scheduled for this campaign day (invitation goes out that morning).
        public Beat For(int day) => _beats.FirstOrDefault(b => b.Day == day);

        /// The beat whose window is open right now, if any.
        public Beat Open(GameTime now) =>
            _beats.FirstOrDefault(b => b.State == BeatState.Pending && b.InWindow(now));

        /// The beat that is open now OR opens within `leadHours`.
        ///
        /// A PLAYER LEAVES EARLY, and until now nothing modelled that. The
        /// invitation goes out in the morning and the window is a couple of
        /// hours in the evening — which is generous for somebody who set off
        /// at half past, and impossible for somebody who only starts walking
        /// when the window opens and has to cross a district.
        ///
        /// It is what made the CI bot look like it could not path: the sim
        /// runs at twenty game-minutes a real second, so a two-hour evening
        /// window is SIX REAL SECONDS of walking. Nobody crosses Hook Street
        /// in six seconds. The beat was unreachable by arithmetic, not by
        /// geometry, and four fixes went into the geometry first.
        public Beat Soon(GameTime now, int leadHours)
        {
            var open = Open(now);
            if (open != null) return open;
            foreach (var b in _beats)
            {
                if (b.State != BeatState.Pending || b.Day != now.Day) continue;
                int until = b.StartHour - now.Hour;
                if (until > 0 && until <= leadHours) return b;
            }
            return null;
        }

        /// Close out any pending beat whose window has passed. Returns those skipped
        /// this call so the caller can narrate them.
        public List<Beat> ResolveLapsed(Func<string, Gossiper> host, GameTime now)
        {
            var lapsed = new List<Beat>();
            foreach (var b in _beats)
                if (b.State == BeatState.Pending && b.WindowPassed(now))
                {
                    b.Skip(host?.Invoke(b.HostId), now);
                    if (b.State == BeatState.Skipped) lapsed.Add(b);
                }
            return lapsed;
        }
    }
}
