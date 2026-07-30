using System;

namespace Ledger.Core
{
    /// SOUNDS WITH NO WORDS IN THEM — audit item 4.
    ///
    /// `weapons-spec.md` §6.2 gives four redundant channels telling you that
    /// you have been noticed, and calls the redundancy the point: any two of
    /// them should be enough. Then:
    ///
    ///   1. the street goes quiet     — sound, and not speech
    ///   2. a bark                    — sound, and speech
    ///   3. a behaviour break         — motion
    ///   4. a music stem              — sound, and not speech
    ///
    /// Three of the four are audio. The project's answer has been
    /// "subtitles-first", and subtitles render channel 2 only: they are for
    /// what was SAID. Nobody subtitles a room going silent. So for a deaf
    /// player the four channels are one channel and a spec that calls itself
    /// redundant is not.
    ///
    /// The spec's own fallback is an optional eye at the frame edge. That is
    /// worth having and it is not an answer — it replaces four channels with
    /// one icon, which is the exact HUD the section spends two pages arguing
    /// against, handed to the players who need the design most.
    ///
    /// SO: CAPTION THE SOUNDS. Not subtitles — captions, the distinction
    /// every accessibility standard draws and this project had not. Three
    /// rules, and each of them is a design decision rather than a formatting
    /// one:
    ///
    ///   **Every caption carries a direction.** In a game whose central
    ///   question is "who noticed, and from where", a caption reading
    ///   "[footsteps]" with no bearing is worse than nothing: it tells a
    ///   player something is happening and denies them the one thing hearing
    ///   would have given them for free. Spatial audio's whole contribution
    ///   is direction, so the caption's whole job is direction.
    ///
    ///   **Every caption carries how loud.** Loudness is not flavour here.
    ///   The noise ring exists because how far a sound carried is a mechanic,
    ///   and a caption that flattens a slam and a scuff into the same line
    ///   throws that mechanic away for the player reading it.
    ///
    ///   **Not everything gets captioned.** A caption per footstep is a wall
    ///   of text that hides the one line that mattered — the same failure the
    ///   mix's voice budget exists to prevent, in a different medium. The
    ///   threshold is the one the game already uses: a sound is captioned
    ///   when it is audible OVER the ambient floor, by `Perception`'s masking
    ///   rule. At 3am a dropped bottle is a caption; at noon it is not, which
    ///   is also true of hearing it.
    public enum CaptionLevel
    {
        /// Nothing. The default, because a player who does not need this
        /// should never be handed it.
        Off,
        /// What people said. This is what the project had, and calling it
        /// "subtitles-first" implied it covered more than it does.
        Speech,
        /// And the sounds that are not speech, which is the level that makes
        /// §6.2's redundancy claim true for a deaf player.
        SpeechAndSound,
    }

    public static class Captions
    {
        /// Where it came from, in words a person can act on.
        ///
        /// Eight arcs, not four. Four leaves "behind" spanning a hundred and
        /// eighty degrees, which is the difference between turning round and
        /// turning the right way — and the noise ring, the gaze cone and the
        /// whole perception model are all directional, so a caption that is
        /// four times vaguer than the simulation is throwing away information
        /// the game already has.
        ///
        /// `bearing` is degrees clockwise from where the player is facing.
        public static string Direction(double bearing)
        {
            double b = bearing % 360.0;
            if (b < 0) b += 360.0;
            // Arc centres at 0/45/90/…; the +22.5 shifts the boundary so the
            // arc is centred on its name rather than starting at it.
            int arc = (int)Math.Floor((b + 22.5) / 45.0) % 8;
            switch (arc)
            {
                case 0: return "ahead";
                case 1: return "ahead right";
                case 2: return "right";
                case 3: return "behind right";
                case 4: return "behind";
                case 5: return "behind left";
                case 6: return "left";
                default: return "ahead left";
            }
        }

        /// How loud, in three words rather than a number.
        ///
        /// Banded against the same decibel scale `Perception` uses, so a
        /// caption cannot disagree with the simulation about what was loud.
        public static string Loudness(double db)
        {
            if (db >= Perception.LoudShout) return "loud";
            if (db >= Perception.LoudConversation) return "";     // the ordinary case: unmarked
            return "faint";
        }

        /// The caption for one sound, or null when it should not be shown.
        ///
        /// Null is the important half. `audibleRadius` is what
        /// `Perception.AudibleRadius` already computed from loudness against
        /// the ambient floor, so a sound the player could not have heard is
        /// not captioned — the caption layer is not an X-ray, it is the same
        /// information in a different sense.
        public static string ForSound(CaptionLevel level, string kind, double db,
                                      double bearing, double metres, double audibleRadius)
        {
            if (level != CaptionLevel.SpeechAndSound) return null;
            if (string.IsNullOrEmpty(kind)) return null;
            if (audibleRadius <= 0 || metres > audibleRadius) return null;

            string what = Describe(kind);
            if (what == null) return null;
            string loud = Loudness(db);
            string where = Direction(bearing);
            return loud.Length > 0
                 ? "[" + loud + " " + what + " — " + where + "]"
                 : "[" + what + " — " + where + "]";
        }

        /// The sound's name in the caption.
        ///
        /// A CLOSED SET, and closed against what the game actually emits
        /// rather than against what a sound library might contain. Three
        /// kinds reach `Perceivers.Emit` today — alarm, slam, speech — and
        /// the rest are the events `Perception` already gives a decibel
        /// figure to, so every entry here corresponds to something the
        /// simulation models. Inventing captions for sounds nothing makes is
        /// how a table drifts away from the game underneath it.
        ///
        /// An unknown kind returns null rather than printing its own internal
        /// identifier at the player, which is how "[sfx_door_03]" ends up in
        /// a shipped screenshot.
        public static string Describe(string kind)
        {
            switch (kind)
            {
                // Emitted today.
                case "speech": return "voices";
                case "slam": return "a door slamming";
                case "alarm": return "shouting";
                // Named by Perception's loudness table, so they carry a real
                // decibel figure the moment anything emits them.
                case "footstep": return "footsteps";
                case "shout": return "a shout";
                case "glass": return "breaking glass";
                case "shot": return "a gunshot";
                default: return null;
            }
        }

        /// THE HARD ONE: the street going quiet is an ABSENCE of sound, and
        /// there is nothing to hang a caption on. It is also §6.2's best
        /// idea and the channel the section leans on hardest.
        ///
        /// So it gets captioned from the hush fraction directly, and it gets
        /// captioned in BOTH directions — the spec is explicit that the
        /// street resuming is how the player learns the event is over, which
        /// is the half games are chronically bad at. A deaf player who is
        /// told they were noticed and never told it passed is worse off than
        /// one who was told neither.
        ///
        /// Returns null while nothing is happening, so a caller can drive
        /// this every frame.
        public const double HushCaptionAt = 0.35;
        public const double HushClearBelow = 0.12;

        public static string ForHush(CaptionLevel level, double hush, bool alreadyShown)
        {
            if (level != CaptionLevel.SpeechAndSound) return null;
            if (!alreadyShown && hush >= HushCaptionAt) return "[the street goes quiet]";
            if (alreadyShown && hush <= HushClearBelow) return "[the street picks up again]";
            return null;
        }

        /// And the fourth channel. One low stem enters when somebody's
        /// attention is genuinely on you; nothing else in the mix is allowed
        /// to do that, which is exactly what makes it captionable without
        /// ambiguity. Deliberately vague about WHO — the music does not know
        /// either, and a caption that says more than the channel it stands in
        /// for is a different, better channel handed only to some players.
        public static string ForAttentionStem(CaptionLevel level, bool entering) =>
            level != CaptionLevel.SpeechAndSound ? null
            : entering ? "[the music turns]" : null;
    }
}
