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
    public enum Space
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
        public static double DecaySeconds(Space s) =>
            s == Space.Outdoors ? 0.5 :
            s == Space.Alley ? 0.8 :
            s == Space.Room ? 1.2 :
            2.6;

        /// How much of the signal is reflected, 0..1. The alley's trick is a
        /// SHORT decay with a HIGH wet mix — lots of reflection arriving fast
        /// — which is what makes it read as narrow rather than as large.
        public static double Wetness(Space s) =>
            s == Space.Outdoors ? 0.10 :
            s == Space.Alley ? 0.45 :
            s == Space.Room ? 0.30 :
            0.55;

        /// Metres. Drives the pre-delay: how long before the first reflection
        /// comes back, which is the cue the ear uses to judge room size.
        public static double RoomMetres(Space s) =>
            s == Space.Outdoors ? 3.0 :
            s == Space.Alley ? 4.0 :
            s == Space.Room ? 7.0 :
            22.0;

        /// Which space you are standing in, from the street network we already
        /// have. Lanes are four metres wide between two building faces, which
        /// is an alley whatever the map calls it — so the most recognisable
        /// acoustic in the game comes free from data authored for pathfinding.
        public static Space SpaceFor(string edgeKind, double metresFromCentreline)
        {
            // Well off any street: a yard, a lot, open ground. Under the sky.
            if (edgeKind == null || metresFromCentreline > 6.0) return Space.Outdoors;
            return edgeKind == "lane" ? Space.Alley : Space.Outdoors;
        }

        /// Indoor spaces are also quieter about the outside world. Used to
        /// duck the street bed when the player steps through a door, which is
        /// the single clearest signal that they have entered somewhere.
        public static double OutsideBleed(Space s) => s == Space.Outdoors ? 1.0 : 0.28;
    }
}
