using System;

namespace Ledger.Core
{
    /// TWO PEOPLE TALKING, as a thing you can SEE.
    ///
    /// This game's entire thesis is that the antagonist is gossip. The mill
    /// has run since the first week: rumours pass along a contact graph,
    /// confidence decays, contradictions expose lies. All of it invisible.
    /// The street shows a dozen people walking past each other in silence
    /// while, underneath, the thing the game is about is happening
    /// constantly.
    ///
    /// Some of it was already audible — `GossipDirector` makes two walkers
    /// speak lines when a rumour about the PLAYER passes within earshot. But
    /// they say it while facing away from each other and walking on, because
    /// until now there was no body to point.
    ///
    /// So this is the posture layer, and the case for it is not decoration:
    /// a player who can watch two strangers stop, turn in, and lean toward
    /// each other has been shown the game's central mechanic without a line
    /// of UI. And it applies to EVERY exchange, not only ones about him —
    /// a city that only ever talks about you is a city with one subject.
    public static class Confab
    {
        /// How far apart people stand to talk, metres, centre to centre.
        ///
        /// Proxemics, not guesswork: personal distance runs about 0.45m to
        /// 1.2m and that is where a conversation between acquaintances sits.
        /// Closer is intimate and reads as a threat or a courtship; further
        /// is social distance and reads as two strangers who happen to be
        /// standing near each other, which is exactly what the street looks
        /// like now.
        public const double NearMetres = 0.85;
        public const double FarMetres = 1.30;

        /// Distance for one exchange. A secret is told CLOSER — people lean
        /// in for the thing they should not be saying, and that lean is
        /// legible from across a street even when the words are not.
        public static double Distance(double tie, bool sensitive)
        {
            double t = Feel.Clamp01(tie);
            double d = FarMetres - (FarMetres - NearMetres) * t;
            if (sensitive) d -= 0.18;
            // The lower arm of this clamp is belt-and-braces: the curve
            // bottoms out at NearMetres - 0.18 on its own, so it never binds.
            // A break run proved that by widening it to 0.15m with every
            // check still green. It stays as a statement of the limit, and
            // the test pins the CURVE's floor rather than the clamp's.
            return Feel.Clamp(d, NearMetres - 0.20, FarMetres);
        }

        /// How far off the direct line each speaker stands, degrees.
        ///
        /// NOT NOSE TO NOSE. Two people squared up dead-on is the posture of
        /// an argument, and a city where every conversation is staged that
        /// way reads as a city on the edge of a fight. Real conversation sits
        /// slightly offset — shoulders angled, one foot back — and the
        /// difference between the two is most of what tells a viewer whether
        /// what they are watching is friendly.
        public const double OffAxisDegrees = 19;

        /// And an argument IS square-on, which makes the same number do the
        /// work twice: when a confrontation happens, the shoulders come round
        /// and the player reads it before anybody says anything.
        public static double OffAxis(bool hostile) => hostile ? 3 : OffAxisDegrees;

        /// How long they stand there. Longer for close contacts and for
        /// things worth saying quietly.
        public const double MinSeconds = 2.2;
        public const double MaxSeconds = 9.0;

        public static double Seconds(double tie, bool sensitive)
        {
            double t = Feel.Clamp01(tie);
            double s = MinSeconds + (MaxSeconds - MinSeconds) * (0.35 + 0.45 * t);
            if (sensitive) s += 1.6;
            return Feel.Clamp(s, MinSeconds, MaxSeconds);
        }

        /// Turning in and breaking off both take a moment. A pair that snaps
        /// to face each other and snaps apart reads as two objects being
        /// repositioned, which is what it is, and the whole job here is to
        /// stop it looking like that.
        public const double TurnSeconds = 0.55;
        public const double PartSeconds = 0.75;

        /// How committed the pose is at time `t` into a confab of length
        /// `total`. Rises, holds, falls.
        public static double Commitment(double t, double total)
        {
            if (t < 0 || t >= total) return 0;
            double inP = Feel.Clamp01(t / TurnSeconds);
            double outP = Feel.Clamp01((total - t) / PartSeconds);
            return Smooth(Math.Min(inP, outP));
        }

        /// WHO WALKS TO WHOM. The listener goes to the speaker, not the other
        /// way round and not both meeting in the middle.
        ///
        /// Both moving is the obvious implementation and it looks wrong for a
        /// reason worth naming: it reads as choreography, because two people
        /// converging on a point neither of them occupied is something that
        /// only happens when someone has arranged it. Somebody with news
        /// stands still and somebody who wants it comes over.
        public static bool ListenerApproaches => true;

        /// The furthest apart two people can be and still start one. Beyond
        /// this the walk over would be the whole event, and a pair crossing a
        /// street to deliver one line looks like a fetch quest.
        public const double StartWithinMetres = 6.5;

        /// And nobody stops mid-road. A confab needs somewhere to stand, and
        /// the middle of a carriageway is not it — which matters because the
        /// rumour graph does not know where anybody is and will happily fire
        /// an exchange between two people crossing a junction.
        public static bool WorthStopping(double metresApart, bool bothOnFoot,
                                         bool somewhereToStand)
        {
            if (!bothOnFoot || !somewhereToStand) return false;
            return metresApart <= StartWithinMetres;
        }

        static double Smooth(double t)
        {
            t = Feel.Clamp01(t);
            return t * t * (3 - 2 * t);
        }
    }
}
