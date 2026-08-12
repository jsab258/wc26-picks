using System;

namespace Ledger.Core
{
    /// THE EDGES OF A SPOKEN LINE, FEATHERED — because Jafar heard the pop.
    ///
    /// The decoder hands back a waveform that starts and ends wherever the
    /// model happened to leave it, which is almost never zero. Played raw,
    /// the jump from silence to that first sample is a step discontinuity —
    /// an audible click at the top of EVERY live line. It was found by ear in
    /// a five-line test file ("a slight pop at the beginning of each one")
    /// and the game's own playback path had the identical fault waiting:
    /// `PumpSpeech` built the clip from the raw samples and played it.
    ///
    /// The repair is the standard one: a short raised-cosine ramp at each
    /// edge. Ten milliseconds up and twenty down — under any perceptual
    /// threshold for onset shaping, far above the one-sample step that
    /// clicks. In Core rather than in `Audio` because it is pure arithmetic
    /// on an array, which means it can be TESTED here instead of waiting
    /// twenty-eight minutes to be wrong.
    public static class SpeechSamples
    {
        /// In place, deliberately: the worker thread owns this buffer and it
        /// is about to be copied into an AudioClip; a second allocation per
        /// line would be pure cost.
        public static void Feather(float[] samples, int sampleRate,
                                   double fadeInMs = 10.0, double fadeOutMs = 20.0)
        {
            if (samples == null || samples.Length == 0 || sampleRate <= 0) return;
            int up = (int)(sampleRate * fadeInMs / 1000.0);
            int down = (int)(sampleRate * fadeOutMs / 1000.0);
            // A MUTTER MUST SURVIVE ITS OWN FADES. On a clip shorter than the
            // ramps, each is clamped to half the clip, so the two never
            // overlap and the middle sample keeps its value.
            if (up > samples.Length / 2) up = samples.Length / 2;
            if (down > samples.Length / 2) down = samples.Length / 2;
            for (int i = 0; i < up; i++)
            {
                double g = 0.5 - 0.5 * Math.Cos(Math.PI * i / up);
                samples[i] = (float)(samples[i] * g);
            }
            for (int i = 0; i < down; i++)
            {
                double g = 0.5 - 0.5 * Math.Cos(Math.PI * i / down);
                samples[samples.Length - 1 - i] =
                    (float)(samples[samples.Length - 1 - i] * g);
            }
        }
    }
}
