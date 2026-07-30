using System;

namespace Ledger.Core
{
    /// Where a sound is, and what the place does to it (game-feel-spec.md §4).
    ///
    /// The spec's line was that "nothing sells a PLACE faster" than the bar
    /// sounding like a room and the alley sounding like an alley. That is
    /// true, but it undersells what this is for here, because LEDGER's
    /// antagonist is gossip and gossip travels by ear.
    ///
    /// So this is not decoration. **How well you heard something is how
    /// confident the rumour you carry away should be.** A line caught across
    /// a wet street through traffic is a half-heard thing, and a half-heard
    /// thing is exactly what the gossip mill already models — it has taken a
    /// confidence argument since the day it was written and nothing has ever
    /// had a principled number to put in it. Now the geometry supplies one.
    ///
    /// It doubles as the cover for the voice work: a bark at fifteen metres
    /// is quiet and low-passed, and a low-passed bark is a bark whose TTS
    /// seams nobody can hear. See production-plan-audio-art.md §1d.
    public enum SpaceKind
    {
        /// The street. Almost no reverb — the sky is not a ceiling.
        Outdoors,
        /// The bar, a back office, a flat.
        Room,
        /// Narrow, hard, parallel walls: little decay but a bright slapback.
        /// The most recognisable acoustic in the game.
        Alley,
        /// A warehouse, the station hall. Long and washy.
        Hall,
    }

    public static class Acoustics
    {
        /// How far a normal speaking voice carries outdoors before it stops
        /// being words and starts being noise. Deliberately short: if you can
        /// hear the whole street you are not in a city, you are in a menu.
        public const double SpeechCarry = 14.0;

        /// A raised voice, an argument, somebody shouting across a road.
        public const double ShoutCarry = 34.0;

        /// Below this you cannot make out words, only that talking happened.
        /// That distinction is the mechanic: knowing a conversation occurred
        /// is not the same as knowing what was said, and the gossip mill has
        /// always been able to represent the difference.
        public const double WordsThreshold = 0.45;

        /// Volume with distance. Not true inverse-square — that is correct
        /// physics and terrible game audio, because it makes everything
        /// either deafening or inaudible with almost nothing in between.
        public static double Gain(double metres, double carry)
        {
            if (carry <= 0) return 0;
            if (metres <= 0) return 1;
            double d = metres / carry;
            return Feel.Clamp01(1.0 / (1.0 + 2.2 * d * d));
        }

        /// Air eats high frequencies with distance, and a wall eats most of
        /// what is left. The cutoff IS the sense of distance — a quiet sound
        /// that is still bright reads as a small sound nearby, not a loud one
        /// far away, and getting this wrong is why so much game audio feels
        /// like it is playing inside the player's head.
        public static double LowPassHz(double metres, bool occluded)
        {
            double open = 22000.0;
            double far = 1100.0;
            double t = Feel.Clamp01(metres / (SpeechCarry * 1.6));
            double hz = open + (far - open) * Math.Sqrt(t);
            // A wall is not a distance. It is a different, much harder filter,
            // which is why muffled-through-a-door is instantly recognisable.
            if (occluded) hz = Math.Min(hz, 700.0);
            return hz;
        }

        /// 0..1: how much of the words you actually got.
        ///
        /// streetNoise is the chatter/traffic bed, 0..1 — the same number the
        /// audio mixer already uses, so a loud street genuinely does make
        /// eavesdropping harder rather than only sounding as though it does.
        public static double Intelligibility(double metres, bool occluded,
                                             double streetNoise = 0.0,
                                             double carry = SpeechCarry)
        {
            if (carry <= 0) return 0;
            double clarity = Feel.Clamp01(1.0 - metres / carry);
            // Faster than linear, but not squared. Squared was the first
            // attempt and it put the edge of intelligibility at about four
            // metres, which meant you could not follow a conversation from
            // the other end of the bar you own.
            clarity = Math.Pow(clarity, 1.5);
            if (occluded) clarity *= 0.25;
            clarity *= 1.0 - 0.5 * Feel.Clamp01(streetNoise);
            return Feel.Clamp01(clarity);
        }

        public static bool CanMakeOutWords(double metres, bool occluded,
                                           double streetNoise = 0.0,
                                           double carry = SpeechCarry) =>
            Intelligibility(metres, occluded, streetNoise, carry) >= WordsThreshold;

        /// What a listener at this distance should record in the gossip mill.
        ///
        /// Capped below certainty on purpose: overhearing is never knowledge.
        /// GossipMill promotes anything at 0.95 or above into hard knowledge,
        /// and a thing you heard across a room must never become a thing you
        /// know — that distinction is most of what makes the mill feel like
        /// rumour rather than a database.
        public static double OverheardConfidence(double metres, bool occluded,
                                                 double streetNoise = 0.0,
                                                 double carry = SpeechCarry)
        {
            double i = Intelligibility(metres, occluded, streetNoise, carry);
            if (i < WordsThreshold * 0.5) return 0;     // heard nothing usable
            return Feel.Clamp(0.25 + 0.65 * i, 0.0, 0.9);
        }

        /// Above this you got the line. Below it you got some of it.
        const double Verbatim = 0.88;

        /// The line as the listener ACTUALLY HEARD IT.
        ///
        /// This is the piece that makes the whole model visible instead of
        /// merely audible. Half-hearing a sentence is not the same as hearing
        /// it quietly, and rendering a distant line at full text in a smaller
        /// font tells the player they have perfect ears and only bad eyes.
        /// Dropping words puts the gap where it belongs — in what they know —
        /// and it is a better hook than certainty ever was, because a
        /// sentence with a hole in it makes you walk closer.
        ///
        /// Returns null when nothing usable came through: you heard talking,
        /// not words, and the caller should show no line at all.
        public static string AsHeard(string line, double intelligibility, int seed)
        {
            if (string.IsNullOrWhiteSpace(line)) return null;
            if (intelligibility >= Verbatim) return line;
            if (intelligibility < WordsThreshold * 0.5) return null;

            double p = Feel.Clamp((Verbatim - intelligibility) / 0.66, 0.0, 0.75);
            var words = line.Split(' ');
            var rng = new Random(seed);
            var sb = new System.Text.StringBuilder();
            bool gap = false, kept = false;
            foreach (var w in words)
            {
                if (w.Length == 0) continue;
                if (rng.NextDouble() < p)
                {
                    // Collapse a run of lost words into one ellipsis rather
                    // than a stutter of them — a listener does not perceive
                    // four separate absences, only one gap.
                    if (!gap) { if (sb.Length > 0) sb.Append(' '); sb.Append('…'); gap = true; }
                    continue;
                }
                if (sb.Length > 0) sb.Append(' ');
                sb.Append(w);
                gap = false; kept = true;
            }
            // Losing every word is indistinguishable from hearing nothing, and
            // a bubble containing one ellipsis is noise on the screen.
            if (!kept) return null;
            return sb.ToString();
        }

        // ---- what the place does to it ----

        /// Reverb decay in seconds. Outdoors is not zero: a street between
        /// buildings has a real, short tail, and setting it to nothing is why
        /// so many outdoor scenes sound like a recording booth.
        public static double DecaySeconds(SpaceKind s) =>
            s == SpaceKind.Outdoors ? 0.5 :
            s == SpaceKind.Alley ? 0.8 :
            s == SpaceKind.Room ? 1.2 :
            2.6;

        /// How much of the signal is reflected, 0..1. The alley's trick is a
        /// SHORT decay with a HIGH wet mix — lots of reflection arriving fast
        /// — which is what makes it read as narrow rather than as large.
        public static double Wetness(SpaceKind s) =>
            s == SpaceKind.Outdoors ? 0.10 :
            s == SpaceKind.Alley ? 0.45 :
            s == SpaceKind.Room ? 0.30 :
            0.55;

        /// Metres. Drives the pre-delay: how long before the first reflection
        /// comes back, which is the cue the ear uses to judge room size.
        public static double RoomMetres(SpaceKind s) =>
            s == SpaceKind.Outdoors ? 3.0 :
            s == SpaceKind.Alley ? 4.0 :
            s == SpaceKind.Room ? 7.0 :
            22.0;

        /// Which space you are standing in, from the street network we already
        /// have. Lanes are four metres wide between two building faces, which
        /// is an alley whatever the map calls it — so the most recognisable
        /// acoustic in the game comes free from data authored for pathfinding.
        public static SpaceKind SpaceFor(string edgeKind, double metresFromCentreline)
        {
            // Well off any street: a yard, a lot, open ground. Under the sky.
            if (edgeKind == null || metresFromCentreline > 6.0) return SpaceKind.Outdoors;
            return edgeKind == "lane" ? SpaceKind.Alley : SpaceKind.Outdoors;
        }

        /// Indoor spaces are also quieter about the outside world. Used to
        /// duck the street bed when the player steps through a door, which is
        /// the single clearest signal that they have entered somewhere.
        public static double OutsideBleed(SpaceKind s) => s == SpaceKind.Outdoors ? 1.0 : 0.28;

        // ---- THE SECOND CHANNEL: what a telephone does to a voice ----------
        //
        // The phone is not decoration. design-doc calls it "the second
        // channel" and it has its own milestone; `PhoneBook` already models
        // the SOCIAL half of it — FidelityOnTheLine, how much less you learn
        // down a wire than face to face. What did not exist anywhere in the
        // project was the ACOUSTIC half. A voice on the phone was
        // sample-identical to the same voice standing in the room, which
        // throws away the mechanic's entire identity: the one sound every
        // player on earth can identify inside half a second, rendered as if
        // the handset were not there.
        //
        // Everything below is the same shape as the distance model above —
        // constants a mixer can read, no DSP — and the Game layer turns it
        // into filters.

        /// The passband of a telephone, and these are not invented numbers:
        /// 300–3400 Hz is the ITU voice channel, the thing the whole world's
        /// telephony was built to carry and the reason a phone sounds like a
        /// phone. Everything below 300 takes the chest out of a voice;
        /// everything above 3400 takes the sibilance, which is where most of
        /// the consonants live.
        public const double TelephoneLowHz = 300.0;
        public const double TelephoneHighHz = 3400.0;

        /// A handset is a small hard cavity held against a face, and it rings
        /// — a broad peak in the low mids that is as much of the "phone"
        /// signature as the band limit is. Without it a band-passed voice
        /// sounds like a voice through a wall rather than like a telephone.
        public const double HandsetResonanceHz = 1400.0;
        public const double HandsetResonanceQ = 1.6;

        /// What kind of line you are on, worst to best. Which one you get is
        /// a fact about the fiction — who is calling, from where — and it is
        /// the whole reason this is an enum and not a float.
        public enum LineKind
        {
            /// A phone in a place you own, on a line you pay for.
            Handset,
            /// A callbox on a street. Coins, traffic behind it, and worse
            /// carbon in the mouthpiece.
            PayPhone,
            /// Trunk call. Thin, delayed, and slightly the wrong speed.
            LongDistance,
            /// Wet junction box, bad exchange, somebody on an extension.
            BadLine,
        }

        /// The best clarity this line can deliver — the ceiling that distance
        /// never gets to raise.
        ///
        /// A GOOD LINE IS DELIBERATELY ABOVE `Verbatim`. The temptation is to
        /// put every phone call under the elision threshold because a real
        /// telephone genuinely is less intelligible than a face; the result
        /// would be that every line of the game's second core mechanic
        /// arrives with a hole in it, and a mechanic that is annoying every
        /// time is not a mechanic. So the good handset is clean text with a
        /// telephone's SOUND, and the degradation is spent where it means
        /// something — the callbox, the trunk, the bad junction.
        public static double LineClarity(LineKind line)
        {
            switch (line)
            {
                case LineKind.Handset: return 0.94;
                case LineKind.PayPhone: return 0.80;
                case LineKind.LongDistance: return 0.68;
                default: return 0.45;              // BadLine
            }
        }

        /// Hiss and hum on the wire, 0..1. Not a fault to be minimised — it
        /// is the floor the voice sits on, and a phone call with a silent
        /// background is the single most obvious tell that nobody treated it.
        public static double LineNoise(LineKind line)
        {
            switch (line)
            {
                case LineKind.Handset: return 0.06;
                case LineKind.PayPhone: return 0.14;
                case LineKind.LongDistance: return 0.22;
                default: return 0.40;
            }
        }

        /// DISTANCE DOES NOT EXIST ON A LINE, and this exists to say so out
        /// loud where somebody would otherwise reach for `Intelligibility`.
        /// A caller two hundred miles away and a caller in the next street
        /// arrive at the same volume; that is what a telephone IS. The
        /// street noise at the LISTENER's end still applies, because that is
        /// in the room with their ear, and the noise at the caller's end
        /// arrives as `Bleed` below.
        public static double LineIntelligibility(LineKind line,
                                                 double listenerNoise = 0.0)
        {
            double clarity = LineClarity(line);
            clarity *= 1.0 - 0.35 * Feel.Clamp01(listenerNoise);
            // Half the weight the in-room model gives street noise: a handset
            // is pressed to the ear and shields it, which is why people put a
            // finger in the other one and why it works.
            return Feel.Clamp01(clarity);
        }

        /// WHOSE VOICE WAS THAT — the mechanic the band limit buys us.
        ///
        /// Recognising a familiar voice leans on exactly what 300–3400 Hz
        /// throws away: the top octave where breath and sibilance live, and
        /// the bottom where the chest is. This is why anonymous calls work in
        /// every crime story ever written, and it is free here.
        ///
        /// `familiarity` is 0..1 — a stranger, an acquaintance, your brother.
        public static bool CanPlaceTheVoice(LineKind line, double familiarity)
        {
            double needed;
            switch (line)
            {
                case LineKind.Handset: needed = 0.35; break;
                case LineKind.PayPhone: needed = 0.55; break;
                case LineKind.LongDistance: needed = 0.70; break;
                default: needed = 0.95; break;     // BadLine: near enough never
            }
            return Feel.Clamp01(familiarity) >= needed;
        }

        /// HOW MUCH OF THE CALLER'S ROOM COMES DOWN THE WIRE.
        ///
        /// The best detail available to a game whose subject is knowing where
        /// people are: a jukebox behind Ellis tells you which bar he is
        /// standing in, and nobody had to write a line of dialogue saying so.
        /// A hall bleeds most — its reverb is long enough to survive the
        /// band limit — and a room bleeds least, which is why an empty office
        /// sounds like nowhere.
        ///
        /// Scaled by the line, because a bad junction buries the room along
        /// with everything else.
        public static double Bleed(SpaceKind caller, LineKind line)
        {
            double room;
            switch (caller)
            {
                case SpaceKind.Hall: room = 0.55; break;
                case SpaceKind.Outdoors: room = 0.45; break;
                case SpaceKind.Alley: room = 0.30; break;
                default: room = 0.20; break;       // Room
            }
            return Feel.Clamp01(room * (1.0 - 0.6 * LineNoise(line)));
        }

        /// The line as the person on the other end of a telephone heard it —
        /// the same elision `AsHeard` does in a room, driven by the wire
        /// instead of by metres. A good handset returns the line whole.
        public static string AsHeardOnTheLine(string line, LineKind kind,
                                              double listenerNoise, int seed) =>
            AsHeard(line, LineIntelligibility(kind, listenerNoise), seed);
    }
}
