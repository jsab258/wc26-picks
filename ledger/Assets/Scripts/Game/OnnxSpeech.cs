#if LEDGER_ONNX
using System;
using System.Collections.Generic;
using Ledger.Core;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

namespace Ledger.Game
{
    /// THE THREE GRAPHS, DRIVEN. This is the last piece of live speech and it
    /// is deliberately the dumbest one: every decision — sampling, stopping,
    /// budget, routing, what is worth saying — is in Core, and this hands
    /// tensors to onnxruntime and copies numbers back.
    ///
    /// BEHIND A COMPILE SWITCH, and that is not timidity. Three DLLs totalling
    /// 32 MB are fetched by CI — measured, after I twice wrote ~250 MB from
    /// memory — and a Game layer that will not compile without them is a Game
    /// layer nobody can build. `LEDGER_ONNX` is defined by the build job once
    /// they are verified on disk; without it the field in `Audio` stays null
    /// and every route falls back to the bank, which is what it does today.
    ///
    /// WHAT EACH GRAPH IS, because the split is not obvious from its name:
    ///
    ///   t3-prefill    the sentence and the voice, into the model's working
    ///                 memory of them. Once per line, and the expensive one.
    ///   t3-step       one token and its position, into the next token's
    ///                 odds. Hundreds of times per line.
    ///   s3gen-decode  every token at once, into samples you can hear.
    ///
    /// THE CACHE IS NEVER COPIED TO MANAGED MEMORY. Sixty tensors, and at
    /// three hundred steps each is about 3 MB — turning them into C# arrays
    /// every step would allocate roughly sixty gigabytes over one sentence and
    /// spend the whole line in the collector. They stay as onnxruntime's own
    /// values, and the previous step's are disposed once the next step has
    /// been fed. That ordering is the whole of the memory management here and
    /// getting it backwards frees a tensor while it is being read.
    public class OnnxSpeech : ISpeechBackend, IDisposable
    {
        readonly InferenceSession _prefill;
        readonly InferenceSession _step;
        readonly InferenceSession _decode;
        readonly Func<string, VoiceConditionals> _voice;
        readonly Func<string, int[]> _tokenize;

        /// The names the graphs were exported with. Checked at load rather
        /// than trusted, because a graph that runs under different names is a
        /// graph this cannot drive and the failure would otherwise be a
        /// runtime exception on the first line somebody speaks.
        const string TextTokens = "text_tokens";
        const string SpeakerEmb = "speaker_emb";
        const string CondTokens = "cond_speech_tokens";
        const string EmotionAdv = "emotion_adv";

        readonly string[] _cacheIn;      // cache0..cacheN on the step graph
        readonly string[] _cacheOut;     // newcache0..newcacheN
        readonly int _layers;

        /// The live cache, as onnxruntime's own values. Null between lines.
        IDisposableReadOnlyCollection<DisposableNamedOnnxValue> _held;
        VoiceConditionals _current;
        int _steps;

        public int VocabSize { get { return SpeechVocab.Size; } }
        public int StopToken { get { return SpeechVocab.Stop; } }

        /// TWO, AND IT IS CLASSIFIER-FREE GUIDANCE RATHER THAN BATCHING. Both
        /// graphs run the transformer on the sentence and on a copy with the
        /// conditioning removed; Core steers between them. Combining here
        /// would hide the one part of the sampler that can be checked without
        /// a GPU.
        public int Rows { get { return 2; } }

        /// Why the backend is unusable, or null. Kept because "no model on
        /// disk" and "the model refused to load" want different fixes and
        /// both otherwise present as a game that never speaks.
        public string Why { get; private set; }

        public static OnnxSpeech Open(string folder,
                                      Func<string, VoiceConditionals> voice,
                                      Func<string, int[]> tokenize,
                                      out string why)
        {
            why = null;
            try
            {
                var p = System.IO.Path.Combine(folder, "t3-prefill.onnx");
                var s = System.IO.Path.Combine(folder, "t3-step.onnx");
                var d = System.IO.Path.Combine(folder, "s3gen-decode.onnx");
                foreach (var f in new[] { p, s, d })
                {
                    if (!System.IO.File.Exists(f))
                    {
                        why = "no " + System.IO.Path.GetFileName(f) + " in " + folder;
                        return null;
                    }
                }
                var me = new OnnxSpeech(p, s, d, voice, tokenize);
                why = me.Why;
                return me.Why == null ? me : null;
            }
            catch (Exception e)
            {
                why = e.GetType().Name + ": " + e.Message;
                return null;
            }
        }

        OnnxSpeech(string prefill, string step, string decode,
                   Func<string, VoiceConditionals> voice, Func<string, int[]> tokenize)
        {
            _voice = voice;
            _tokenize = tokenize;
            var opts = new SessionOptions();
            // DirectML when the machine has it, CPU when it does not. The probe
            // measured CPU BEATING DirectML per step 4.4x on this model and
            // nobody knows why yet, so this is not a speed decision — it is
            // that a machine without the runtime must still fall back rather
            // than fail to construct.
            try { opts.AppendExecutionProvider_DML(0); }
            catch (Exception) { /* CPU it is */ }

            _prefill = new InferenceSession(prefill, opts);
            _step = new InferenceSession(step, opts);
            _decode = new InferenceSession(decode, opts);

            var stepIn = new List<string>();
            foreach (var i in _step.InputMetadata.Keys) stepIn.Add(i);
            _layers = stepIn.Count - 2;
            if (_layers < 1)
            {
                Why = "the step graph has " + stepIn.Count + " inputs, so no cache";
                return;
            }
            _cacheIn = new string[_layers];
            _cacheOut = new string[_layers];
            for (int i = 0; i < _layers; i++)
            {
                _cacheIn[i] = "cache" + i;
                _cacheOut[i] = "newcache" + i;
                if (!_step.InputMetadata.ContainsKey(_cacheIn[i]))
                { Why = "the step graph has no '" + _cacheIn[i] + "'"; return; }
                if (!_step.OutputMetadata.ContainsKey(_cacheOut[i]))
                { Why = "the step graph has no '" + _cacheOut[i] + "'"; return; }
                if (!_prefill.OutputMetadata.ContainsKey(_cacheIn[i]))
                { Why = "the prefill graph has no '" + _cacheIn[i] + "'"; return; }
            }
            foreach (var n in new[] { TextTokens, SpeakerEmb, CondTokens, EmotionAdv })
                if (!_prefill.InputMetadata.ContainsKey(n))
                { Why = "the prefill graph has no '" + n + "'"; return; }
            // AN OLD PREFILL IS REFUSED AT LOAD, WITH ITS SYMPTOM NAMED. The
            // first export returned a cache and no odds, and a line spoken
            // through it lost its opening words while every gate stayed green.
            // Failing here says which file is stale; failing at the first
            // spoken line says only that speech is off.
            if (!_prefill.OutputMetadata.ContainsKey("logits"))
            { Why = "the prefill graph has no 'logits': it is an old export, "
                    + "and lines from it start a word or two in"; return; }
            if (!_step.InputMetadata.ContainsKey("token")
                || !_step.InputMetadata.ContainsKey("position"))
            { Why = "the step graph does not take a token and a position"; return; }
        }

        /// The types come off the GRAPH rather than from memory. The text
        /// tokens are int32 because `text_to_tokens` returns an `IntTensor`,
        /// and the prompt tokens are int64 because they came from somewhere
        /// else — two integer widths in one file, and assuming either one is
        /// how the audit tool crashed on its first real run.
        static DenseTensor<long> Longs(VoiceConditionals.Array3 a)
        {
            var t = new DenseTensor<long>(Dims(a.Shape));
            for (int i = 0; i < a.Longs.Length; i++) t.SetValue(i, a.Longs[i]);
            return t;
        }

        static DenseTensor<float> Floats(VoiceConditionals.Array3 a)
        {
            var t = new DenseTensor<float>(Dims(a.Shape));
            for (int i = 0; i < a.Floats.Length; i++) t.SetValue(i, a.Floats[i]);
            return t;
        }

        static int[] Dims(int[] shape) { return (int[])shape.Clone(); }

        /// The odds, out of whichever graph just ran. Both name this output
        /// `logits` and both give it the same width, so the caller does not
        /// have to know whether this is the first token of the line or the
        /// eightieth — which is the whole reason the prefill was given a head.
        bool Read(IDisposableReadOnlyCollection<DisposableNamedOnnxValue> got,
                  float[] logits)
        {
            foreach (var v in got)
            {
                if (v.Name != "logits") continue;
                var t = v.AsTensor<float>();
                int n = Math.Min(logits.Length, (int)t.Length);
                for (int k = 0; k < n; k++) logits[k] = t.GetValue(k);
                // A SHORT READ IS A FAILURE, NOT A PARTIAL SUCCESS. Half a
                // row of odds sampled against a stale second half would pick
                // words rather than throw, and a wrong word is the hardest
                // fault in this pipeline to trace back to its cause.
                if (n != logits.Length)
                    Why = "the graph gave " + n + " odds, the sampler wants "
                          + logits.Length;
                return n == logits.Length;
            }
            Why = "the graph returned no logits";
            return false;
        }

        public bool Begin(string voiceId, string text, float[] logits)
        {
            Release();
            _steps = 0;
            _current = _voice != null ? _voice(voiceId) : null;
            if (_current == null) { Why = "no voice '" + voiceId + "'"; return false; }
            var ids = _tokenize != null ? _tokenize(text) : null;
            if (ids == null || ids.Length == 0) { Why = "nothing to say"; return false; }

            try
            {
                // THE SENTENCE MARKERS ARE NOT ADDED HERE. The prefill graph
                // pads the start and stop text tokens on inside, where the
                // model's own constants are — one less thing for this side to
                // agree with the model about.
                var tt = new DenseTensor<int>(new[] { 1, ids.Length });
                for (int i = 0; i < ids.Length; i++) tt.SetValue(i, ids[i]);

                var feed = new List<NamedOnnxValue>
                {
                    NamedOnnxValue.CreateFromTensor(TextTokens, tt),
                    NamedOnnxValue.CreateFromTensor(SpeakerEmb,
                        Floats(_current.Get("t3.speaker_emb"))),
                    NamedOnnxValue.CreateFromTensor(CondTokens,
                        Longs(_current.Get("t3.cond_prompt_speech_tokens"))),
                    NamedOnnxValue.CreateFromTensor(EmotionAdv,
                        Floats(_current.Get("t3.emotion_adv"))),
                };
                _held = _prefill.Run(feed);

                // THE PREFILL GIVES THE FIRST TOKEN'S ODDS, AND THE VERSION
                // THAT THREW THEM AWAY IS WHAT JAFAR HEARD. Running the whole
                // sentence produces the odds for the first spoken token as a
                // by-product — `T3.inference` samples from exactly this. The
                // old code here asked for them by taking a step at position 1
                // with the start token, which embeds that token a SECOND time,
                // shifts every later position by one, and loses the word the
                // model had already chosen. The line came out beginning at
                // "van again" instead of "Seen the van again", and no numeric
                // comparison anywhere could see it: both sides agreed about
                // every value that was there, and the fault was a value that
                // was not.
                return Read(_held, logits);
            }
            catch (Exception e)
            {
                Why = "prefill: " + e.GetType().Name + ": " + e.Message;
                Release();
                return false;
            }
        }

        public bool Next(int token, float[] logits)
        {
            if (_held == null) { Why = "no line in progress"; return false; }
            try
            {
                var tok = new DenseTensor<long>(new[] { 1, 1 });
                tok.SetValue(0, token);
                var pos = new DenseTensor<long>(new int[0]);   // a scalar
                pos.SetValue(0, ++_steps);

                var feed = new List<NamedOnnxValue>
                {
                    NamedOnnxValue.CreateFromTensor("token", tok),
                    NamedOnnxValue.CreateFromTensor("position", pos),
                };
                int i = 0;
                foreach (var v in _held)
                {
                    // THE ODDS ARE NOT PART OF THE CACHE, and both graphs put
                    // them first. Skipping by NAME rather than by index is the
                    // difference between this working and feeding a 6,563-wide
                    // logits tensor in as layer zero's keys — which is what a
                    // positional loop did the day the prefill grew an output.
                    if (v.Name == "logits") continue;
                    // The prefill names the rest `cacheN` and the step names
                    // its own `newcacheN`, so the name to feed under is this
                    // side's, taken by position rather than by the name the
                    // value happens to carry.
                    feed.Add(NamedOnnxValue.CreateFromTensor(
                        _cacheIn[i], v.AsTensor<float>()));
                    i++;
                    if (i >= _layers) break;
                }
                if (i < _layers)
                {
                    Why = "the graph returned " + i + " cache tensors, not " + _layers;
                    Release();
                    return false;
                }

                var got = _step.Run(feed);
                // ORDER MATTERS AND IS THE WHOLE OF THE MEMORY MANAGEMENT.
                // The old values are still being read while `Run` executes,
                // so they are released only once it has returned.
                var old = _held;
                _held = got;
                old.Dispose();

                return Read(got, logits);
            }
            catch (Exception e)
            {
                Why = "step " + _steps + ": " + e.GetType().Name + ": " + e.Message;
                Release();
                return false;
            }
        }

        public void Release()
        {
            if (_held != null) { _held.Dispose(); _held = null; }
        }

        /// TOKENS INTO SAMPLES, and the noise comes from here rather than from
        /// inside the graph.
        ///
        /// The flow decoder starts from Gaussian noise and the vocoder's
        /// source module adds more — that is what a neural source-filter
        /// vocoder IS, not a flaw. Left inside, the same line would sound
        /// different every time and nothing about the conversion would be
        /// checkable. Handed in, the line is reproducible from a seed, which
        /// is `VoiceBank`'s determinism rule reaching the last stage.
        ///
        /// A third draw happens inside the vocoder and is discarded there —
        /// `s, _, _ = self.m_source(s)` at both of its call sites — so it is
        /// not an input and the game does not spend three megabytes a line
        /// generating numbers nothing reads.
        public float[] Decode(int[] tokens)
        {
            if (tokens == null || tokens.Length == 0) return null;
            if (_current == null) { Why = "no voice to decode with"; return null; }
            try
            {
                var pt = _current.Get("gen.prompt_token");
                var pf = _current.Get("gen.prompt_feat");
                var em = _current.Get("gen.embedding");
                if (pt == null || pf == null || em == null)
                { Why = "the voice has no s3gen half"; return null; }

                // MEASURED, NOT DERIVED. The mel length is two frames per
                // token MINUS the prompt's own mel count, which is not the
                // same as twice the prompt's tokens: of the nineteen voices
                // one has 419 frames against 418 tokens' worth, because the
                // extractor and the tokeniser disagree by a frame on that
                // clip. Doubling would be right for eighteen of them.
                int promptTokens = pt.Rows;
                int promptMels = pf.Rows;
                int h = 2 * (promptTokens + tokens.Length);
                int wav = (h - promptMels) * SamplesPerMel;
                if (wav <= 0) { Why = "the prompt is longer than the line"; return null; }

                // `int * uint` widens to LONG in C#, because uint cannot hold
                // a negative int — so this needs the cast before the multiply
                // rather than around it. Caught by ShapeCheck in seconds once
                // it was told to read conditional code, which is the whole
                // argument for having done that.
                var seed = new Gauss(unchecked((uint)tokens.Length * 2654435761u
                                               + (uint)promptTokens));
                var z = new DenseTensor<float>(new[] { 1, 80, h });
                for (int i = 0; i < 80 * h; i++) z.SetValue(i, seed.Next());
                var sine = new DenseTensor<float>(new[] { 1, Harmonics, wav });
                for (int i = 0; i < Harmonics * wav; i++) sine.SetValue(i, seed.Next());

                var tk = new DenseTensor<long>(new[] { 1, tokens.Length });
                for (int i = 0; i < tokens.Length; i++) tk.SetValue(i, tokens[i]);

                using (var got = _decode.Run(new List<NamedOnnxValue>
                {
                    NamedOnnxValue.CreateFromTensor("tokens", tk),
                    NamedOnnxValue.CreateFromTensor("prompt_token", Longs(pt)),
                    NamedOnnxValue.CreateFromTensor("prompt_feat", Floats(pf)),
                    NamedOnnxValue.CreateFromTensor("embedding", Floats(em)),
                    NamedOnnxValue.CreateFromTensor("z", z),
                    NamedOnnxValue.CreateFromTensor("sine_noise", sine),
                }))
                {
                    foreach (var v in got)
                    {
                        var t = v.AsTensor<float>();
                        var outp = new float[t.Length];
                        for (int i = 0; i < outp.Length; i++) outp[i] = t.GetValue(i);
                        return outp;
                    }
                }
                Why = "the decode graph returned nothing";
                return null;
            }
            catch (Exception e)
            {
                Why = "decode: " + e.GetType().Name + ": " + e.Message;
                return null;
            }
        }

        /// 480 samples of audio per mel frame, from the shipped vocoder's
        /// upsample rates [8,5,3] times its tiny inverse STFT hop of 4. The
        /// class default is [8,8], which gives 256 — measured rather than
        /// remembered, because a test built from the defaults spent a while
        /// proving a neighbouring vocoder correct.
        const int SamplesPerMel = 480;

        /// Nine harmonic bands, which is the source module's `harmonic_num + 1`.
        const int Harmonics = 9;

        /// Gaussian noise from a seed, so a line is repeatable.
        ///
        /// Box-Muller rather than a sum of uniforms: the sum is cheaper and
        /// has no tails, and the tails are where an excitation signal does its
        /// work. It runs about three million times a line, which sounds like a
        /// lot until it is set against the nine seconds the model spends.
        struct Gauss
        {
            uint _s;
            float _spare;
            bool _has;

            public Gauss(uint seed) { _s = seed == 0 ? 1u : seed; _spare = 0f; _has = false; }

            float Unit()
            {
                _s ^= _s << 13; _s ^= _s >> 17; _s ^= _s << 5;
                return (_s & 0xFFFFFF) / 16777216f;
            }

            public float Next()
            {
                if (_has) { _has = false; return _spare; }
                float u = Unit(), v = Unit();
                if (u < 1e-7f) u = 1e-7f;
                float r = (float)Math.Sqrt(-2.0 * Math.Log(u));
                float a = (float)(2.0 * Math.PI * v);
                _spare = r * (float)Math.Sin(a);
                _has = true;
                return r * (float)Math.Cos(a);
            }
        }

        public void Dispose()
        {
            Release();
            if (_prefill != null) _prefill.Dispose();
            if (_step != null) _step.Dispose();
            if (_decode != null) _decode.Dispose();
        }
    }
}
#endif
