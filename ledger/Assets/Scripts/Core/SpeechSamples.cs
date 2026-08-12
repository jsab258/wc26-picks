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
        /// THE HEAD IS MUTED, NOT JUST FADED, AND THE NUMBER CAME FROM A
        /// FILE. Measured in the five-line test wav: every line opens with a
        /// ~16ms transient (peaks ~0.02) at the very top of the decode,
        /// followed by real silence, then speech ~100ms in. That is the
        /// vocoder starting cold — its source filter rings for a frame or
        /// two, which is exactly why upstream streaming carries a
        /// `cache_source` between chunks. In silence it reads as a pop; when
        /// a word follows closely the ear parses click-then-word as a
        /// truncated word, which is how one artifact produced two different
        /// complaints. A fade only scales it; 25ms of hard zero removes it,
        /// and every observed word onset sits safely past 90ms.
        public static void Feather(float[] samples, int sampleRate,
                                   double fadeInMs = 10.0, double fadeOutMs = 20.0,
                                   double muteHeadMs = 25.0)
        {
            if (samples == null || samples.Length == 0 || sampleRate <= 0) return;
            int mute = (int)(sampleRate * muteHeadMs / 1000.0);
            int up = (int)(sampleRate * fadeInMs / 1000.0);
            int down = (int)(sampleRate * fadeOutMs / 1000.0);
            // A MUTTER MUST SURVIVE ITS OWN REPAIRS. The mute is clamped to a
            // quarter of the clip and the ramps to half, so the three can
            // never meet in the middle and silence a whole short word.
            if (mute > samples.Length / 4) mute = samples.Length / 4;
            if (up > samples.Length / 2 - mute) up = Math.Max(0, samples.Length / 2 - mute);
            if (down > samples.Length / 2) down = samples.Length / 2;
            for (int i = 0; i < mute; i++) samples[i] = 0f;
            for (int i = 0; i < up; i++)
            {
                double g = 0.5 - 0.5 * Math.Cos(Math.PI * i / up);
                samples[mute + i] = (float)(samples[mute + i] * g);
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
