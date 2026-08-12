using System.Collections.Generic;

namespace Ledger.Core
{
    /// One decode call of a streamed line: see the line up to
    /// `VisibleTokens`, skip the `MelOffset` mels already rendered, and only
    /// the final call keeps the last lookahead's worth.
    public struct SpeechChunk
    {
        public int VisibleTokens;
        public int MelOffset;
        public bool Final;
    }

    /// HOW A LINE BECOMES PIECES, AND WHEN THE FIRST PIECE MAY PLAY.
    ///
    /// The step loop now runs at ~17ms a token on the resident path — 58
    /// tokens a second against playback's 25 — so the voice can outrun its
    /// own speech. What turns that margin into a character who STARTS
    /// talking under a second is chunked decoding: render the first ~24
    /// tokens' audio while the rest of the line is still being sampled.
    /// The decode side is `s3gen-chunk.onnx`; this file is the arithmetic
    /// that drives it, in Core because every line of it is testable without
    /// a GPU and wrong boundaries are a click at every seam.
    ///
    /// `Plan` MIRRORS `tools/voice-live/hear-chunks.py plan_chunks` — the
    /// python is what the listening test runs, this is what the game runs,
    /// and they carry each other's names so a change greps its way to the
    /// twin. One idea in two implementations is this project's most-paid
    /// fault; the twin being named is the mitigation.
    public static class SpeechStream
    {
        /// The model's ratios, same sources as `OnnxSpeech`'s copies.
        public const int MelsPerToken = 2;
        public const int SamplesPerMel = 480;

        /// `flow.pre_lookahead_len`, read off the shipped model. A
        /// non-final chunk's last three tokens render provisionally, so
        /// their mels are held back and re-rendered by the next call.
        public const int LookaheadTokens = 3;

        /// ~0.96s of audio a piece. Small enough that the first piece is
        /// ready fast, large enough that the flow's re-render overhead —
        /// each call re-encodes everything so far — stays a fraction of the
        /// audio it yields.
        public const int ChunkTokens = 24;

        /// Which decode calls a line of `tokens` becomes. Empty for an
        /// empty line; a line at or under one chunk is a single final call.
        public static List<SpeechChunk> Plan(int tokens,
                                            int chunk = ChunkTokens,
                                            int lookahead = LookaheadTokens)
        {
            var plan = new List<SpeechChunk>();
            if (tokens <= 0) return plan;
            int done = 0, seen = 0;
            while (true)
            {
                seen = seen + chunk < tokens ? seen + chunk : tokens;
                bool final = seen >= tokens;
                int avail = MelsPerToken * seen
                    - (final ? 0 : MelsPerToken * lookahead);
                if (final || avail > done)
                {
                    plan.Add(new SpeechChunk
                    { VisibleTokens = seen, MelOffset = done, Final = final });
                    done = avail;
                }
                if (final) return plan;
            }
        }

        /// THE NO-UNDERRUN RULE: playback may begin when the work still
        /// owed is less than the audio already banked plus the audio that
        /// work will yield — then the buffer cannot empty before the line
        /// ends, by construction rather than by margin.
        ///
        /// `bankedSeconds` is decoded audio not yet played;
        /// `remainingWorkSeconds` is the projection for every step and
        /// decode still owed; `remainingAudioSeconds` is what that work
        /// yields. All three come from `SpeechDirector`'s measured rates —
        /// this is arithmetic on measurements, not a policy number.
        public static bool CanStart(double bankedSeconds,
                                    double remainingWorkSeconds,
                                    double remainingAudioSeconds)
        {
            return bankedSeconds > 0
                && remainingWorkSeconds < bankedSeconds + remainingAudioSeconds;
        }

        /// Whether streaming is worth attempting AT ALL on this machine —
        /// the generation rate must beat playback's 25 tokens a second, or
        /// the stream underruns mid-line and a character stutters, which
        /// reads worse than the same character pausing before a whole
        /// line. Rates come measured from `SpeechDirector`; zero means
        /// unmeasured, and an unmeasured machine does not stream.
        public static bool Sustainable(double stepsPerSecond,
                                       double tokensPerStep)
        {
            double tokensPerSecond = stepsPerSecond * tokensPerStep;
            // 25 tokens of audio play per second (the model's 25Hz token
            // rate), with a sixth of headroom so scheduling noise on a
            // borderline machine does not turn into a mid-word stutter.
            return tokensPerSecond > 25.0 * 1.15;
        }
    }
}
