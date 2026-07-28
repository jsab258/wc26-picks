using System;

namespace Ledger.Core
{
    /// ADAPTIVE SCORE — the music as an instrument of the simulation.
    ///
    /// The score exists and is a fixed day/night pair, which makes it
    /// wallpaper. In a game whose antagonist is GOSSIP, the music has a job
    /// nobody else can do: **tell the player the street has turned before the
    /// interface does.** That is the same principle M15 was built on — the
    /// simulation is the interface — applied to the one channel that reaches
    /// a player who is looking somewhere else.
    ///
    /// THE COMPOSITION RULE THIS FILE IS BUILT ON, and it is the opposite of
    /// what most games do: **as exposure rises, the score LOSES instruments.**
    /// Total energy goes DOWN, not up. A stinger and a wall of strings say
    /// "something dramatic is happening"; a room going quiet says "everybody
    /// here knows". The second is far more frightening and it is what this
    /// street would actually do.
    public enum MusicLayer
    {
        /// The pad. The city exists and is indifferent to you.
        Bed = 0,
        /// Bass and arpeggio. Momentum, ordinary business, a night that is
        /// going to plan. The FIRST thing to go when it stops going to plan.
        Pulse = 1,
        /// A high detuned drone. The street is talking about you.
        Unease = 2,
        /// A low swell. Not "you are in danger" — "this is already decided".
        Dread = 3,
    }

    /// Everything the score is allowed to know. Deliberately small: a score
    /// that reads twenty variables is a score nobody can predict, and a
    /// player who cannot predict the music cannot learn to read it.
    public class ScoreState
    {
        /// How loudly the day circle is talking about you, 0..1.
        public double Heat;
        /// The strongest story anybody is carrying that would stand up, 0..1.
        public double StrongestLead;
        /// 0 = none, up through the police inquiry stages.
        public Inquiry Police = Inquiry.None;
        /// Somebody within sight is at Confronts or Refuses.
        public bool Cornered;
        /// Days left on the audit, or -1 when it has not opened.
        public int DaysLeftOnAudit = -1;
        public double Night;
        /// Talking to somebody: the score gets out of the way.
        public bool InConversation;
    }

    public static class MusicModel
    {
        public const int Layers = 4;

        /// How fast a layer moves toward its target, per second. Slow on
        /// purpose — music that snaps between states is worse than no music,
        /// and the player should notice the change afterwards rather than
        /// during.
        public const double SettleRate = 0.22;
        /// Dread arrives faster than it leaves. It is allowed to be the one
        /// thing that gets your attention.
        public const double DreadInRate = 0.55;

        /// Below this a layer is silent rather than nearly silent — a pad at
        /// 2% is not atmosphere, it is a mix problem you cannot hear and
        /// cannot debug.
        public const double Floor = 0.02;

        /// THE MIX. Returns a target gain per layer, 0..1.
        public static double[] Mix(ScoreState s)
        {
            var g = new double[Layers];
            if (s == null) return g;

            double heat = Feel.Clamp01(s.Heat);
            double lead = Feel.Clamp01(s.StrongestLead);
            // One number for "how known are you", because heat and a
            // testimony-grade lead are two views of the same pressure and
            // mixing them separately makes the score jitter.
            double exposure = Feel.Clamp01(Math.Max(heat, lead * 0.9));

            // Real, present danger — a different axis from being talked
            // about. You can be completely exposed and perfectly safe.
            double threat = 0;
            if (s.Police >= Inquiry.Manhunt) threat = 1.0;
            else if (s.Police >= Inquiry.Investigation) threat = 0.7;
            else if (s.Police >= Inquiry.Procedure) threat = 0.3;
            if (s.Cornered) threat = Math.Max(threat, 0.6);
            if (s.DaysLeftOnAudit >= 0)
                threat = Math.Max(threat, Feel.Clamp01((6 - s.DaysLeftOnAudit) / 6.0) * 0.8);

            // BED — always there, until it is not. Above three-quarters
            // exposed the pad thins out, and that thinning IS the signal.
            g[(int)MusicLayer.Bed] = 1.0 - 0.75 * Feel.Clamp01((exposure - 0.55) / 0.45);

            // PULSE — the sound of a night going to plan, and therefore the
            // first thing to leave when it stops going to plan. A player who
            // has heard the arpeggio drop out twice will feel the third time
            // before they know why.
            g[(int)MusicLayer.Pulse] =
                Feel.Clamp01(1.0 - exposure * 1.5) * (1.0 - 0.6 * threat);

            // UNEASE — rises with being talked about, and only that.
            g[(int)MusicLayer.Unease] = Feel.Clamp01((exposure - 0.2) / 0.6);

            // DREAD — the only layer that answers to danger rather than to
            // talk, so it means one thing and keeps meaning it.
            g[(int)MusicLayer.Dread] = Feel.Clamp01(threat * threat);

            // Talking: everything drops but nothing stops. The score should
            // be under the conversation, not paused for it — a hard cut to
            // silence tells the player a cutscene has started.
            if (s.InConversation)
                for (int i = 0; i < Layers; i++) g[i] *= 0.45;

            // Night takes the top off rather than adding to the bottom.
            double night = Feel.Clamp01(s.Night);
            g[(int)MusicLayer.Pulse] *= 1.0 - 0.35 * night;

            for (int i = 0; i < Layers; i++)
            {
                g[i] = Feel.Clamp01(g[i]);
                if (g[i] < Floor) g[i] = 0;
            }
            return g;
        }

        /// TOTAL ENERGY, which is the property this whole file exists to
        /// hold. Exposed as its own function because it is the thing worth
        /// asserting, and a mix that quietly stops obeying it would otherwise
        /// only be caught by ear.
        public static double Energy(double[] mix)
        {
            if (mix == null) return 0;
            double sum = 0;
            // Weighted: a pad at full is not as much MUSIC as an arpeggio at
            // full, and an unweighted sum would let a swelling drone count as
            // the same energy as a rhythm section.
            double[] weight = { 0.8, 1.4, 0.7, 0.9 };
            for (int i = 0; i < mix.Length && i < weight.Length; i++) sum += mix[i] * weight[i];
            return sum;
        }

        /// Move the live mix toward the target. Frame-rate independent, same
        /// as everything else here.
        public static void Settle(double[] live, double[] target, double seconds)
        {
            if (live == null || target == null) return;
            for (int i = 0; i < live.Length && i < target.Length; i++)
            {
                double rate = (i == (int)MusicLayer.Dread && target[i] > live[i])
                    ? DreadInRate : SettleRate;
                live[i] = Feel.Clamp01(Feel.Approach(live[i], target[i], rate, seconds));
            }
        }

        /// A room that has gone quiet. Named because it is a STATE the design
        /// cares about, not an incidental consequence of the numbers — this is
        /// the moment the player should learn to dread.
        public static bool RoomHasGoneQuiet(double[] mix) =>
            mix != null && mix.Length >= Layers
            && mix[(int)MusicLayer.Pulse] <= Floor
            && mix[(int)MusicLayer.Unease] > 0.5;
    }
}
