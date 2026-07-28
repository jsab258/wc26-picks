using System;

namespace Ledger.Core
{
    /// THE MIX (the-gap.md §3c — audio scored 4, "closable").
    ///
    /// The bark bank is blocked on a listening pass that is not mine to do.
    /// The MIX is not blocked on anything, and it is most of why an
    /// independent game sounds independent: every source is authored at a
    /// hardcoded level, nothing gets out of the way of anything else, and a
    /// busy street turns into a wall.
    ///
    /// What is here today is one boolean — `Audio.DuckMusic(talking)` — and
    /// a per-source volume constant. That is the whole mixing desk.
    ///
    /// THREE THINGS FIX MOST OF IT, and all three are arithmetic:
    ///
    ///   **Ducking that does not pump.** A duck with symmetric attack and
    ///   release breathes audibly on every line; the fix is old and cheap and
    ///   universal — drop fast, come back slow.
    ///
    ///   **A budget on how many things may speak at once.** Forty people on a
    ///   street is forty footsteps, and the important sound loses to the
    ///   forty unimportant ones by arriving last.
    ///
    ///   **Summing that matches hearing rather than arithmetic.** Ten sounds
    ///   at 0.3 do not make 3.0; they make about 0.95. Adding them linearly
    ///   is why crowds clip.
    public enum Bus
    {
        /// Anybody speaking — the player's conversations, barks, overheard
        /// gossip. The bus everything else gets out of the way of.
        Voice = 0,
        /// Footsteps, cloth, keys, doors. Close, small, constant.
        Foley = 1,
        /// Hits, drops, collisions. Loud and brief.
        Impact = 2,
        /// The street bed, rain, traffic. Continuous and unimportant.
        Ambience = 3,
        /// The adaptive score.
        Music = 4,
        /// Menus and notifications. Outside the world, so outside the duck.
        Ui = 5,
    }

    public static class Mixing
    {
        public const int Buses = 6;

        // ---- ducking --------------------------------------------------------

        /// Seconds to duck DOWN, and seconds to come back.
        ///
        /// ASYMMETRIC, AND THIS IS THE WHOLE THING. Equal times make the mix
        /// breathe on every syllable — the bed swelling into each gap and
        /// collapsing again, which is the most recognisable sound of an
        /// amateur mix and is audible to people who could not name it. Get
        /// out of the way immediately; come back so slowly nobody notices you
        /// left.
        public const double DuckAttackSeconds = 0.08;
        public const double DuckReleaseSeconds = 0.75;

        /// How far each bus gets out of the way of a voice, 0 = untouched.
        ///
        /// NOT UNIFORM. Music ducks hard because it is the thing competing
        /// for the same frequencies and the same attention. Ambience ducks a
        /// little — take it out entirely and the street falls silent behind
        /// the speaker, which sounds like a bug and is the classic
        /// over-correction. Foley barely ducks at all: footsteps under
        /// dialogue are what stop a conversation feeling like it happens in a
        /// vacuum. And UI does not duck, because it is not in the world.
        public static double DuckDepth(Bus bus)
        {
            switch (bus)
            {
                case Bus.Music: return 0.65;
                case Bus.Ambience: return 0.30;
                case Bus.Impact: return 0.15;
                case Bus.Foley: return 0.10;
                default: return 0.0;   // Voice and Ui
            }
        }

        /// OVERHEARING IS A DIFFERENT DUCK, and it is the one this game
        /// actually needs. Two people discussing the player six metres away
        /// is the moment the entire gossip system exists for, and it is
        /// competing with rain, traffic and a street bed authored to sit at a
        /// comfortable level for walking around in.
        ///
        /// So the bed gets out of the way HARDER for something the player was
        /// not meant to hear than for a conversation he is having. Leaning in
        /// to catch something is a real thing ears do and the mix should do
        /// it too.
        public static double OverhearDepth(Bus bus)
        {
            switch (bus)
            {
                case Bus.Music: return 0.80;
                case Bus.Ambience: return 0.62;
                case Bus.Impact: return 0.25;
                case Bus.Foley: return 0.20;
                default: return 0.0;
            }
        }

        /// One frame of a duck envelope. `target` is 0..1 how far down we
        /// want to be; `current` is where we are.
        ///
        /// Frame-rate independent by the same `1 - exp(-k*dt)` this project
        /// uses everywhere, so a duck sounds the same at 30fps and 240.
        public static double StepDuck(double current, double target, double dt)
        {
            if (dt <= 0) return current;
            double t = Feel.Clamp01(target);
            double c = Feel.Clamp01(current);
            double seconds = t > c ? DuckAttackSeconds : DuckReleaseSeconds;
            double k = 1.0 - Math.Exp(-dt / Math.Max(1e-4, seconds));
            return Feel.Clamp01(c + (t - c) * k);
        }

        /// The gain multiplier for a bus at a given duck amount.
        public static double Gain(Bus bus, double duck, bool overhearing)
        {
            double depth = overhearing ? OverhearDepth(bus) : DuckDepth(bus);
            return Feel.Clamp01(1.0 - depth * Feel.Clamp01(duck));
        }

        // ---- how many things may speak at once -------------------------------

        /// Concurrent one-shots allowed per bus.
        ///
        /// Forty people on a street is forty footsteps, and the platform will
        /// happily play all of them — at which point the one sound that
        /// mattered arrives last, gets whatever voice is left, and is
        /// inaudible under thirty-nine identical scuffs. A budget is not a
        /// performance measure, it is a mixing decision.
        public static int Budget(Bus bus)
        {
            switch (bus)
            {
                case Bus.Voice: return 4;
                case Bus.Foley: return 8;
                case Bus.Impact: return 6;
                case Bus.Ambience: return 4;
                case Bus.Music: return 8;
                default: return 4;
            }
        }

        /// Whether a new sound gets a voice, given how many are already
        /// playing on that bus and what the quietest of them is.
        ///
        /// STEALING IS FROM THE BOTTOM. A new sound louder than the quietest
        /// one playing takes its slot; a new sound quieter than everything
        /// already going is dropped, because it would have been inaudible
        /// anyway and playing it would only cost the slot.
        ///
        /// Returns true to play, and sets `steal` when something has to stop.
        public static bool Admit(Bus bus, double loudness, int playing,
                                 double quietestPlaying, out bool steal)
        {
            steal = false;
            if (playing < Budget(bus)) return true;
            // Full. Only worth it if this is louder than what it displaces.
            if (loudness <= quietestPlaying) return false;
            steal = true;
            return true;
        }

        /// AND PRIORITY OVERRIDES ALL OF IT. An authored line must never lose
        /// its voice to a footstep, however loud the footstep is and however
        /// full the bus.
        ///
        /// A separate mechanism from loudness on purpose: an important line
        /// spoken quietly is exactly the case that matters, and a system that
        /// ranks by volume alone throws away precisely the sound worth
        /// protecting.
        public static bool Protected(Bus bus, bool authored) =>
            authored && (bus == Bus.Voice || bus == Bus.Ui);

        // ---- summing that matches hearing ------------------------------------

        /// The gain to apply to `n` simultaneous copies of a sound so the
        /// result sits where one copy of it did.
        ///
        /// INCOHERENT SOURCES SUM AS THE SQUARE ROOT OF THEIR COUNT, not as
        /// their count — ten footsteps at 0.3 make roughly 0.95, not 3.0.
        /// Adding them linearly is why a crowd clips and why the usual fix
        /// (turn everything down until the crowd is safe) leaves a single
        /// walker inaudible.
        public static double CrowdGain(int n)
        {
            if (n <= 1) return 1.0;
            return 1.0 / Math.Sqrt(n);
        }

        /// Total ceiling across all buses. Anything over this is scaled back
        /// as a whole rather than clipped, because clipping a mix is the one
        /// artefact no amount of good sound design survives.
        public const double Headroom = 0.92;

        public static double Limit(double summed)
        {
            if (summed <= Headroom) return 1.0;
            // Scales the WHOLE mix rather than the offending source, so the
            // balance between buses survives a loud moment instead of the
            // loudest thing being singled out and everything else jumping
            // forward — which is pumping again, wearing a different hat.
            return Headroom / summed;
        }

        // ---- distance ---------------------------------------------------------

        /// How far a bus carries, in metres, before it is inaudible.
        ///
        /// Voices carry FURTHER than footsteps, which is both true and
        /// necessary: the overheard-gossip mechanic requires a conversation
        /// to be audible from further away than a scuff, or the player has to
        /// stand on top of people to catch anything and the whole channel
        /// becomes a stealth minigame.
        public static double Reach(Bus bus)
        {
            switch (bus)
            {
                case Bus.Voice: return 14;
                case Bus.Impact: return 22;
                case Bus.Foley: return 7;
                case Bus.Ambience: return 40;
                default: return 100;
            }
        }

        /// Attenuation with distance, 1 at the source and 0 at the reach.
        ///
        /// Inverse-distance rather than linear, with a near field that does
        /// not blow up: real sound falls off fast at first and slowly after,
        /// and a linear rolloff is why so many games have a sound that is
        /// either at full volume or gone.
        public static double Attenuate(Bus bus, double metres)
        {
            double reach = Reach(bus);
            if (metres <= 0) return 1.0;
            // Dead for correctness — the fade below already reaches zero at
            // `reach` and clamps beyond it — and kept as an early-out that
            // skips the arithmetic for every sound outside its range, which
            // on a street of forty walkers is most of them. Proved dead by a
            // break run rather than assumed either way.
            if (metres >= reach) return 0.0;
            double inv = 1.0 / (1.0 + metres * 0.55);
            // Forced to zero at the reach so a sound does not hang around at
            // two percent for the width of a district.
            double fade = Feel.Clamp01(1.0 - metres / reach);
            return Feel.Clamp01(inv * fade * (1.0 + 0.55));
        }
    }
}
