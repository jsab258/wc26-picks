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
        /// A VOCALISATION BEFORE THE LINE, CUT AT THE SILENCE THAT PROVES IT
        /// IS NOT PART OF IT. Returns how many samples were removed.
        ///
        /// Jafar, on the five-line take: "there's an 'ah' sound at the
        /// beginning before the 'No.' — the rest is good." He was exactly
        /// right, and the first instrument I pointed at it disagreed with
        /// him: measuring loudness before the onset flagged four lines of
        /// five, because a soft "S" leading into a vowel looks identical to
        /// a spurious noise leading into a word. The number could not answer
        /// the question being asked of it.
        ///
        /// What separates them is a GAP. Printed at 10ms resolution, line
        /// one reads `#######.....###...` — 70ms of sound, 50ms of silence,
        /// then the word at eight times the amplitude. Every other line
        /// reads `.....####...`: silence, then speech that never stops once
        /// it starts. A word does not contain 50ms of silence inside its own
        /// first eighth of a second, so cutting at that gap cannot eat one —
        /// which is the property the old 25ms head-mute lacked, and it ate
        /// an "S" the day after it shipped.
        ///
        /// So the head goes only when all four hold: it starts at the very
        /// top, it ENDS in real silence, that silence lasts at least 30ms,
        /// and the head is a quarter of the body's peak or less. The last
        /// one is what keeps a genuinely quiet first word — someone starting
        /// softly — from being read as a fault.
        ///
        /// One line in five, on the only take that has been measured. That
        /// is a denominator of five and it is written down as such: the
        /// bench reports what it trimmed, so the next runs say whether short
        /// lines are the pattern or that was one render.
        public static int TrimDetachedHead(float[] samples, int sampleRate,
                                           double windowMs = 10.0,
                                           double minGapMs = 30.0,
                                           double lookMs = 250.0)
        {
            if (samples == null || samples.Length == 0 || sampleRate <= 0) return 0;
            int w = (int)(sampleRate * windowMs / 1000.0);
            if (w <= 0) return 0;
            int look = (int)(sampleRate * lookMs / 1000.0);
            if (look > samples.Length) look = samples.Length;
            int wins = look / w;
            if (wins < 4) return 0;

            var rms = new double[wins];
            double loudest = 0;
            for (int i = 0; i < wins; i++)
            {
                double sum = 0;
                for (int j = i * w; j < (i + 1) * w; j++) sum += (double)samples[j] * samples[j];
                rms[i] = Math.Sqrt(sum / w);
                if (rms[i] > loudest) loudest = rms[i];
            }
            // THE BODY'S LEVEL, NOT THE WINDOW'S. `loudest` here is only over
            // the head region; a line whose first quarter-second is all quiet
            // would scale its own threshold down and find a "head" in noise.
            double body = 0;
            for (int i = 0; i < samples.Length; i++)
            {
                double a = Math.Abs(samples[i]);
                if (a > body) body = a;
            }
            if (body <= 0) return 0;
            double quiet = loudest * 0.06;

            int head = 0;
            while (head < wins && rms[head] > quiet) head++;
            if (head == 0) return 0;              // starts in silence: nothing detached
            int gap = head;
            while (gap < wins && rms[gap] <= quiet) gap++;
            if (gap >= wins) return 0;            // never resumes: not a head, just a short clip
            if ((gap - head) * windowMs < minGapMs) return 0;

            double headPeak = 0;
            for (int i = 0; i < head * w; i++)
            {
                double a = Math.Abs(samples[i]);
                if (a > headPeak) headPeak = a;
            }
            if (headPeak > body * 0.25) return 0; // as loud as the line: that IS the line

            int cut = gap * w;                    // through the silence, to the word
            Array.Copy(samples, cut, samples, 0, samples.Length - cut);
            Array.Clear(samples, samples.Length - cut, cut);
            return cut;
        }

        public static void Feather(float[] samples, int sampleRate,
                                   double fadeInMs = 10.0, double fadeOutMs = 20.0,
                                   double muteHeadMs = 25.0)
        {
            if (samples == null || samples.Length == 0 || sampleRate <= 0) return;
            int mute = (int)(sampleRate * muteHeadMs / 1000.0);
            // ONLY WHEN THE HEAD IS AN ISOLATED CLICK, because the mute ate a
            // word. The 25ms figure came from five renders whose speech began
            // 90-380ms in; the very next render started its "S" at zero, the
            // mute cut into it, and Jafar heard a "tch" where the onset used
            // to be. The transient this exists to kill is only AUDIBLE
            // against silence — a render that starts speaking immediately
            // masks it — so the gate is the fault's own definition: a loud
            // first ~16ms followed by near-silence is a click; anything
            // sustained is a voice, and a voice keeps its head.
            int probe = (int)(sampleRate * 0.016);
            int tail = (int)(sampleRate * 0.064);
            if (probe > samples.Length) probe = samples.Length;
            if (tail > samples.Length) tail = samples.Length;
            float clickPeak = 0f, afterPeak = 0f;
            for (int i = 0; i < probe; i++)
                if (Math.Abs(samples[i]) > clickPeak) clickPeak = Math.Abs(samples[i]);
            for (int i = probe; i < tail; i++)
                if (Math.Abs(samples[i]) > afterPeak) afterPeak = Math.Abs(samples[i]);
            bool isolated = afterPeak < 0.01f && clickPeak > afterPeak * 2f;
            if (!isolated) mute = 0;
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
