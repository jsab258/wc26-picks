using System;
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

        /// The vocoder's seam, upstream's `mel_cache_len`: eight cached
        /// mels ride in front of every chunk's fresh ones, and their
        /// samples of source and render carry the waveform across the
        /// boundary. The decode side lives in `OnnxSpeech.DecodeChunk`;
        /// these constants exist so the AUDIO ACCOUNTING below and the
        /// plan's floor agree with it by construction.
        public const int SeamMels = 8;
        public const int SeamSamples = SeamMels * SamplesPerMel;

        /// The samples a chunk actually hands the player, which is NOT its
        /// fresh mels times 480: the first chunk drops the zero-seam's
        /// render and holds a seam back for the next crossfade, middles
        /// emit exactly their fresh samples (the held tail re-emerges
        /// crossfaded at their head), and the final brings the holdback
        /// home. Any release arithmetic that banks `fresh * 480` for the
        /// first chunk overestimates the audio in hand by 160ms and
        /// underruns exactly once, at the start, on every line.
        public static int EmittedSamples(int freshMels, bool first,
                                         bool final)
        {
            // The render always carries the seam ride-in in front.
            int rendered = (SeamMels + freshMels) * SamplesPerMel;
            if (first) rendered -= SeamSamples;    // the zero-seam's render
            if (!final) rendered -= SeamSamples;   // the holdback
            return rendered > 0 ? rendered : 0;
        }

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

        /// See `SpeechChunkFollower` below for the live driver of all of
        /// this; these statics stay separate so the arithmetic is testable
        /// without a decoder in the room.
        ///
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

    /// THE LIVE DRIVER: rides `SpeechLoop` as its sink, decodes a chunk
    /// whenever enough tokens have landed, banks the audio, and answers the
    /// one question playback cares about — may it start yet.
    ///
    /// Decoding happens INSIDE `Tokens`, on the step thread, between steps —
    /// which is the whole design: the two GPU stages must interleave, never
    /// overlap (see `ISpeechStreamSink`). The banked pieces are read from
    /// another thread, so the little state here is under one lock; the
    /// decode call itself is not, because nothing else may touch the
    /// backend while a line is running anyway.
    ///
    /// A DECODER FAILURE IS A ROUTE, NOT AN ERROR: `Failed` flips, no
    /// further chunks are attempted, and the caller finishes the line
    /// through the whole-line decoder it already has. The listener hears
    /// the line a little later rather than not at all.
    public sealed class SpeechChunkFollower : ISpeechStreamSink
    {
        readonly ISpeechChunkDecoder _decoder;
        readonly object _gate = new object();
        readonly List<float[]> _ready = new List<float[]>();
        int _banked;                 // samples decoded and not yet taken
        int _taken;                  // samples handed to playback
        int _nextBoundary = SpeechStream.ChunkTokens;
        int _melOffset;
        bool _first = true;
        bool _started, _failed, _complete;

        // The projection's inputs, all measured by `SpeechDirector` before
        // a stream is attempted — this class does no measuring of its own.
        readonly double _stepsPerSecond, _tokensPerStep;
        readonly double _decodeFixed, _decodePerToken;
        readonly int _expectedTokens;

        public SpeechChunkFollower(ISpeechChunkDecoder decoder,
                                   int expectedTokens,
                                   double stepsPerSecond,
                                   double tokensPerStep,
                                   double decodeFixedSeconds,
                                   double decodeSecondsPerToken)
        {
            _decoder = decoder;
            _expectedTokens = expectedTokens > 0 ? expectedTokens : 1;
            _stepsPerSecond = stepsPerSecond;
            _tokensPerStep = tokensPerStep;
            _decodeFixed = decodeFixedSeconds;
            _decodePerToken = decodeSecondsPerToken;
        }

        /// The decoder said no at some point; the line belongs to the
        /// whole-line path now.
        public bool Failed { get { lock (_gate) return _failed; } }

        /// The final chunk has been decoded; what is banked is the line.
        public bool Complete { get { lock (_gate) return _complete; } }

        /// THE NO-UNDERRUN DECISION, latched: once true it stays true, so
        /// playback cannot flap. True the moment `SpeechStream.CanStart`
        /// says the work still owed fits inside the audio in hand plus the
        /// audio that work yields — EXCEPT on a failed line, which never
        /// offers to start however much it had banked first: the worker
        /// re-speaks a failed line whole, and audio that also started
        /// streaming would say its opening words twice.
        public bool CanStartNow { get { lock (_gate) return _started && !_failed; } }

        /// Samples decoded and not yet taken by playback.
        public int SamplesReady { get { lock (_gate) return _banked; } }

        /// Drain everything banked, in order, as one array — called from
        /// the playback side. Null when nothing is waiting.
        public float[] TakeReady()
        {
            lock (_gate)
            {
                if (_banked == 0) return null;
                var all = new float[_banked];
                int at = 0;
                foreach (var p in _ready)
                { Array.Copy(p, 0, all, at, p.Length); at += p.Length; }
                _ready.Clear();
                _taken += _banked;
                _banked = 0;
                return all;
            }
        }

        /// The sink: called after every kept acoustic token, on the step
        /// thread. Decodes whenever the plan's next boundary has landed.
        public void Tokens(IReadOnlyList<int> tokens)
        {
            if (Failed) return;
            while (tokens.Count >= _nextBoundary)
            {
                Decode(tokens, _nextBoundary, false);
                _nextBoundary += SpeechStream.ChunkTokens;
                if (Failed) return;
            }
        }

        /// The final chunk, after the loop has finished — every token is
        /// visible and the lookahead holds nothing back.
        public void Finish(int[] tokens)
        {
            if (tokens == null || tokens.Length == 0)
            { lock (_gate) _complete = true; return; }
            if (!Failed) Decode(tokens, tokens.Length, true);
            lock (_gate) { _complete = !_failed; _started |= _complete && !_failed; }
        }

        void Decode(IReadOnlyList<int> tokens, int visible, bool final)
        {
            int avail = SpeechStream.MelsPerToken * visible
                - (final ? 0 : SpeechStream.MelsPerToken
                               * SpeechStream.LookaheadTokens);
            if (!final && avail <= _melOffset) return;
            var slice = new int[visible];
            for (int i = 0; i < visible; i++) slice[i] = tokens[i];
            var emitted = _decoder.DecodeChunk(slice, _melOffset, final);
            if (emitted == null) { lock (_gate) _failed = true; return; }
            lock (_gate)
            {
                _ready.Add(emitted);
                _banked += emitted.Length;
                _first = false;
                _melOffset = avail;
                if (!_started)
                {
                    // All three quantities in seconds of audio at the
                    // model's 24kHz. Remaining tokens come from the
                    // caller's expectation and never go below one chunk —
                    // a line that outruns its estimate must still not
                    // start on arithmetic that says it is nearly done.
                    int seen = visible;
                    int remain = _expectedTokens - seen;
                    if (remain < SpeechStream.ChunkTokens && !final)
                        remain = SpeechStream.ChunkTokens;
                    if (remain < 0) remain = 0;
                    double stepSec = _stepsPerSecond > 0
                        ? (remain / (_tokensPerStep > 0 ? _tokensPerStep : 1))
                          / _stepsPerSecond : 0;
                    int chunksLeft = (remain + SpeechStream.ChunkTokens - 1)
                                     / SpeechStream.ChunkTokens;
                    // Each chunk re-renders the whole line so far, so its
                    // cost is charged as a whole-line decode — conservative
                    // on purpose; an early start is the one mistake the
                    // listener can hear.
                    double decSec = chunksLeft
                        * (_decodeFixed + _decodePerToken * _expectedTokens);
                    double banked = (_banked + _taken) / 24000.0;
                    double yield = remain * SpeechStream.MelsPerToken
                        * SpeechStream.SamplesPerMel / 24000.0;
                    if (SpeechStream.CanStart(banked, stepSec + decSec,
                                              yield))
                        _started = true;
                }
            }
        }
    }
}
