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
    ///
    /// AND ON A CARD, "onnxruntime's own values" IS NOT ENOUGH — the classic
    /// `Run` still lands every output in HOST memory, so the cache crosses
    /// PCIe twice a step even though no C# array is ever made. Measured on
    /// the RX 6700: 31.8ms flat plus 142us per position of pure cache
    /// round-trip — a third to a half of every mid-line step is shipping
    /// tensors the next step is about to send straight back. So when
    /// DirectML is present, this binds the cache outputs to DEVICE memory
    /// (`OrtIoBinding`) and feeds the resulting values back as inputs
    /// without a copy; only the logits — 64 KB against the cache's
    /// megabytes — are bound to host, because the sampler lives in Core.
    /// The python preview of this path died in the DML provider
    /// (0xC0000005, both attempts), which is why it is proven through
    /// `SpeechBench` on the real machine before any build leans on it, and
    /// why every managed failure here falls back to the host path with the
    /// reason kept in `Residency`.
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

        // ---- the residency path: the cache stays on the card ----

        /// Whether the DirectML provider actually attached. Without it there
        /// is no device to be resident ON, and the host path is not a
        /// degradation — it is the same speed it ever was.
        readonly bool _dmlOk;

        /// Where device tensors live. "DML" is the provider's own allocator
        /// name; a wrong name here throws at the first bound line and the
        /// catch routes that line — and every later one — through the host
        /// path with the reason kept.
        OrtMemoryInfo _device;
        OrtIoBinding _bindPrefill, _bindStep;
        RunOptions _runOpts;

        /// The PREFILL's outputs: `_vals[0]` is the host logits, `_vals[1..]`
        /// the device cache in layer order. The ORDER IS ASSERTED, not
        /// assumed — `MustMatch` reads the bound names back once per binding
        /// and refuses the path if they differ, because a silent
        /// transposition here is layer 3's keys fed as layer 7's. Disposed
        /// after the first step has consumed them.
        IDisposableReadOnlyCollection<OrtValue> _bound;
        OrtValue[] _vals;

        /// THE CACHE'S REAL HOME: two explicitly-owned device buffer sets,
        /// alternated every step, because the allocator's own buffers are
        /// not to be trusted across runs. Bench rounds one and two both
        /// died at step TWO — the first step, consuming the PREFILL
        /// session's outputs, ran; the second, consuming the step session's
        /// own pool-allocated outputs, hit an {Application Error} inside
        /// layer 0's cache Concat, with and without synchronize calls. The
        /// reading: DirectML's internal allocator treats a run's output
        /// buffers as recyclable scratch for the next run, live references
        /// or not. So the step loop binds its cache outputs into buffers
        /// allocated HERE, exact shape over a max-size block, ping-pong so
        /// a run never reads the half it is writing. Grown only when a
        /// longer prefill needs more room; freed with the session.
        OrtAllocator _dmlAlloc;
        OrtMemoryAllocation[][] _pool;     // [2][layer]
        long[] _poolBytes;                 // capacity per layer, both halves
        long[][] _cacheDims;               // per-layer dims, position axis varies
        int _posAxis = -1;
        long _prefillPos, _pos;
        int _cur = -1;                     // pool half holding the current cache; -1 = prefill values

        /// How many positions past the prefill a bound line may grow. A line
        /// that outgrows it dies quietly and the NEXT line begins bound
        /// again — running out of room is not a broken binding. 512 tokens
        /// is ~20 seconds of speech against a step ceiling of 1000 and
        /// measured lines of ~100.
        const long Room = 512;

        /// The step logits land HERE every run — one pinned host buffer
        /// bound once as the output, no per-step collections to dispose.
        float[] _logitsBuf;
        OrtValue _logitsHome;

        /// Per-line input values. They pin the managed arrays they wrap, so
        /// they live until `Release` — disposing one before `Run` returns
        /// hands the graph freed memory.
        readonly List<IDisposable> _lineInputs = new List<IDisposable>();

        /// The step inputs, made once and MUTATED in place each step — the
        /// value reads its array at run time, so two writes replace two
        /// allocations and two binds per step.
        long[] _tokArr, _posArr;
        OrtValue _tokVal, _posVal;

        bool _lineBound;        // did THIS line begin on the bound path
        bool _bindingBroken;    // a bound line failed; stay on host from here

        /// The bench flips this to time both paths through one session and
        /// to check the bound path's numbers against the host path's — same
        /// graph, same provider, so the logits must agree to float noise.
        public bool ForceHost;

        /// "device", or "host: " and the reason — read by the bench and by
        /// the verdict, because a residency path that quietly stopped being
        /// resident is indistinguishable from a slow card otherwise.
        public string Residency { get; private set; } = "host: no line yet";

        public int VocabSize { get { return SpeechVocab.Size; } }
        public int StopToken { get { return SpeechVocab.Stop; } }

        /// HOW MANY ROWS OF ODDS THE GRAPH GIVES, READ OFF THE GRAPH.
        ///
        /// Two is classifier-free guidance: the transformer runs on the
        /// sentence and on a copy with the conditioning removed, and Core
        /// steers between them. Combining inside here would hide the one part
        /// of the sampler that can be checked without a GPU.
        ///
        /// IT WAS A CONSTANT 2, WHICH WAS TRUE OF EVERY GRAPH THAT HAD EVER
        /// EXISTED. The exporter can now build a one-row pair — half the work
        /// per step, and the biggest remaining lever — and a hardcoded 2
        /// against a one-row graph does not throw. It folds one row of odds
        /// into two half-rows, samples from the wrong half of a vocabulary,
        /// and produces a fluent line of the wrong words. Silent and
        /// plausible is the worst failure this pipeline can have.
        readonly int _rows;
        public int Rows { get { return _rows; } }

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
            // DirectML when the machine has it, CPU when it does not, and
            // BOTH STAGES ON THE SAME ONE — measured on 12 August against the
            // graphs that ship, which is not where the old number came from.
            //
            // An early probe read the CPU beating DirectML 4.4x per step and
            // that reading was quoted for days as a reason to think about
            // splitting the stages. On the real graphs the card is 1.3x
            // FASTER per step (57ms against 77ms) and 3.5x faster at the
            // decode, so there is nothing to split. The old number was
            // measured on a different graph and never re-checked.
            //
            // So this is not a speed decision. It is that a machine without
            // the runtime must fall back rather than fail to construct.
            try { opts.AppendExecutionProvider_DML(0); _dmlOk = true; }
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
            // AND HOW MANY ROWS IT GIVES, BEFORE ANYTHING SAMPLES FROM IT.
            // A dynamic or unexpected first dimension is refused rather than
            // guessed: the wrong row count is not an error at runtime, it is
            // correct-looking speech saying something else.
            var oddsDim = _prefill.OutputMetadata.ContainsKey("logits")
                ? _prefill.OutputMetadata["logits"].Dimensions : null;
            if (oddsDim == null || oddsDim.Length < 1
                || (oddsDim[0] != 1 && oddsDim[0] != 2))
            {
                Why = "the prefill graph gives "
                      + (oddsDim == null || oddsDim.Length < 1
                         ? "no shape for its odds"
                         : oddsDim[0] + " rows of odds, and this drives 1 or 2");
                return;
            }
            _rows = oddsDim[0];
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

            // THE BOUND PATH IS TRIED FIRST AND NEVER TWICE AFTER A FAILURE.
            // A managed exception here — a wrong allocator name, a scalar the
            // binding will not wrap, a provider that has it disabled — costs
            // one attempt and the reason is kept; a NATIVE fault cannot be
            // caught in-process at all, which is what `SpeechBench` exists to
            // rule out on the real machine before a build trusts this.
            if (_dmlOk && !_bindingBroken && !ForceHost)
            {
                try { return BeginBound(ids, logits); }
                catch (Exception e)
                {
                    _bindingBroken = true;
                    Residency = "host: " + e.GetType().Name + ": " + e.Message;
                    ReleaseLine();
                }
            }
            else if (!_dmlOk) Residency = "host: no DirectML";
            else if (ForceHost) Residency = "host: forced";

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
            if (_lineBound)
            {
                try { return NextBound(token, logits); }
                catch (Exception e)
                {
                    // The line is lost — a cache that lives on the card
                    // cannot be handed to the host path mid-sentence — but
                    // the NEXT line is not: it begins on the host path with
                    // the reason kept.
                    _bindingBroken = true;
                    Residency = "host: step " + _steps + ": "
                        + e.GetType().Name + ": " + e.Message;
                    Why = "bound step " + _steps + ": " + e.GetType().Name
                        + ": " + e.Message;
                    Release();
                    return false;
                }
            }
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
            ReleaseLine();
        }

        /// The bound path's per-line state. The bindings, the device info and
        /// the step values survive between lines — they are per-session — but
        /// the cache values and the pinned inputs are this line's only.
        void ReleaseLine()
        {
            if (_bound != null) { _bound.Dispose(); _bound = null; }
            foreach (var v in _lineInputs) v.Dispose();
            _lineInputs.Clear();
            _lineBound = false;
            _cur = -1;
            // The pool, the bindings and the logits home survive between
            // lines — they are per-session, and a conversation reallocates
            // nothing.
        }

        /// Prime the model with the cache bound to the card.
        ///
        /// The prefill's outputs are bound once — logits to host, where the
        /// sampler is, every cache tensor to the device, where the next step
        /// is — and the step graph's identically, so from here to the end of
        /// the line the cache never crosses the bus.
        bool BeginBound(int[] ids, float[] logits)
        {
            if (_device == null)
                _device = new OrtMemoryInfo("DML", OrtAllocatorType.DeviceAllocator,
                                            0, OrtMemType.Default);
            if (_runOpts == null) _runOpts = new RunOptions();
            if (_vals == null) _vals = new OrtValue[_layers + 1];
            if (_bindPrefill == null)
            {
                var b = _prefill.CreateIoBinding();
                b.BindOutputToDevice("logits", OrtMemoryInfo.DefaultInstance);
                for (int i = 0; i < _layers; i++)
                    b.BindOutputToDevice(_cacheIn[i], _device);
                MustMatch(b, _cacheIn);
                _bindPrefill = b;
            }
            if (_tokVal == null)
            {
                // Made HERE, not at the first step, so a wrap the binding
                // refuses — the scalar is the candidate — fails before the
                // line begins and falls back whole, instead of losing a
                // prefill's work at step one.
                _tokArr = new long[1];
                _posArr = new long[1];
                _tokVal = OrtValue.CreateTensorValueFromMemory(
                    _tokArr, new long[] { 1, 1 });
                _posVal = OrtValue.CreateTensorValueFromMemory(
                    _posArr, new long[0]);
            }

            var tt = OrtValue.CreateTensorValueFromMemory(
                ids, new long[] { 1, ids.Length });
            _lineInputs.Add(tt);
            _bindPrefill.BindInput(TextTokens, tt);
            BindArray(_bindPrefill, SpeakerEmb, _current.Get("t3.speaker_emb"));
            BindArray(_bindPrefill, CondTokens,
                      _current.Get("t3.cond_prompt_speech_tokens"));
            BindArray(_bindPrefill, EmotionAdv, _current.Get("t3.emotion_adv"));

            _bound = _prefill.RunWithBoundResults(_runOpts, _bindPrefill);
            // The card may still be writing when Run returns — DirectML
            // batches GPU work — so wait before anything reads or frees
            // what it owes. (This alone did NOT fix the step-two fault;
            // the ping-pong buffers above are what did. Kept because it is
            // the binding API's stated contract for device outputs.)
            _bindPrefill.SynchronizeBoundOutputs();
            Fill(_bound, _vals);

            // Where the pool buffers get their shapes: the position axis
            // from the step graph's metadata (the one dynamic dimension),
            // the rest from the prefill's actual outputs.
            if (_posAxis < 0) FindPosAxis();
            ReadCacheDims();
            EnsurePool();
            if (_logitsHome == null)
            {
                // THE SHAPE IS THE STEP GRAPH'S, NOT AN ASSUMPTION. The
                // prefill emits [rows, vocab] and the step [rows, 1, vocab]
                // — round three bound a rank-2 home for a rank-3 output and
                // was refused by name. Dynamic axes are one token wide at a
                // step; the element count is checked against what the
                // sampler expects, because a home of the right rank and the
                // wrong size would truncate the odds silently.
                var md = _step.OutputMetadata["logits"];
                var dims = new long[md.Dimensions.Length];
                long elems = 1;
                for (int d = 0; d < dims.Length; d++)
                {
                    dims[d] = md.Dimensions[d] < 0 ? 1 : md.Dimensions[d];
                    elems *= dims[d];
                }
                if (elems != (long)_rows * SpeechVocab.Size)
                    throw new InvalidOperationException(
                        "the step graph's logits hold " + elems
                        + " values, the sampler wants "
                        + (long)_rows * SpeechVocab.Size);
                _logitsBuf = new float[elems];
                _logitsHome = OrtValue.CreateTensorValueFromMemory(_logitsBuf, dims);
            }

            _cur = -1;
            _pos = _prefillPos;
            _lineBound = true;
            Residency = "device";
            return ReadBound(_vals[0], logits);
        }

        bool NextBound(int token, float[] logits)
        {
            if (!_lineBound) { Why = "no line in progress"; return false; }
            long inPos = _pos, outPos = _pos + 1;
            if (outPos - _prefillPos > Room)
            {
                // NOT a broken binding — a line that outgrew its room. The
                // line dies, the caller falls back for it, and the next
                // line begins bound again with the pool it already has.
                Why = "the line outgrew the resident cache ("
                      + Room + " steps past the prefill)";
                return false;
            }
            if (_bindStep == null)
            {
                var b = _step.CreateIoBinding();
                b.BindInput("token", _tokVal);
                b.BindInput("position", _posVal);
                b.BindOutput("logits", _logitsHome);
                _bindStep = b;
            }
            _tokArr[0] = token;
            _posArr[0] = ++_steps;

            // THE CACHE NEVER TOUCHES THE ALLOCATOR'S POOL. Inputs read the
            // half that holds the current cache — the prefill's own values
            // on the first step — and outputs write the OTHER half, exact
            // shape bound over a max-size block. Rebinding every step is
            // the point: the shapes grow a position each time.
            int outHalf = _cur < 0 ? 0 : 1 - _cur;
            for (int i = 0; i < _layers; i++)
            {
                if (_cur < 0)
                    _bindStep.BindInput(_cacheIn[i], _vals[i + 1]);
                else
                    _bindStep.BindInput(_cacheIn[i], TensorElementType.Float,
                                        DimsAt(i, inPos), _pool[_cur][i]);
                _bindStep.BindOutput(_cacheOut[i], TensorElementType.Float,
                                     DimsAt(i, outPos), _pool[outHalf][i]);
            }

            _bindStep.SynchronizeBoundInputs();
            _step.RunWithBinding(_runOpts, _bindStep);
            _bindStep.SynchronizeBoundOutputs();

            // The prefill's values are consumed exactly once, by the first
            // step; after the synchronize above the card is done with them.
            if (_cur < 0 && _bound != null) { _bound.Dispose(); _bound = null; }
            _cur = outHalf;
            _pos = outPos;

            int n = Math.Min(logits.Length, _logitsBuf.Length);
            Array.Copy(_logitsBuf, logits, n);
            if (n != logits.Length)
                Why = "the bound step gave " + n + " odds, the sampler wants "
                      + logits.Length;
            return n == logits.Length;
        }

        /// The one dynamic dimension of the step graph's cache outputs is
        /// the position axis. Read from metadata rather than assumed, and
        /// two dynamic axes is a graph this code does not understand —
        /// refused at the first bound line, not guessed at.
        void FindPosAxis()
        {
            var md = _step.OutputMetadata[_cacheOut[0]];
            if (md.ElementDataType != TensorElementType.Float)
                throw new InvalidOperationException(
                    "the cache is " + md.ElementDataType + ", not float");
            var dims = md.Dimensions;
            int ax = -1;
            for (int i = 0; i < dims.Length; i++)
            {
                if (dims[i] >= 0) continue;
                if (ax >= 0)
                    throw new InvalidOperationException(
                        "the cache has two dynamic axes; which is the position?");
                ax = i;
            }
            if (ax < 0)
                throw new InvalidOperationException(
                    "the cache has no dynamic axis, so no room to grow");
            _posAxis = ax;
        }

        /// Every layer's dims, read off the prefill's actual outputs, and
        /// every layer must agree on the position count — a disagreement is
        /// an export this code does not understand.
        void ReadCacheDims()
        {
            if (_cacheDims == null) _cacheDims = new long[_layers][];
            _prefillPos = -1;
            for (int i = 0; i < _layers; i++)
            {
                _cacheDims[i] = _vals[i + 1].GetTensorTypeAndShape().Shape;
                long p = _cacheDims[i][_posAxis];
                if (_prefillPos < 0) _prefillPos = p;
                else if (p != _prefillPos)
                    throw new InvalidOperationException(
                        "layer " + i + " has " + p + " positions, layer 0 has "
                        + _prefillPos);
            }
        }

        /// Two device blocks per layer, sized for this prefill plus `Room`.
        /// GROW-ONLY: a longer prefill replaces the blocks, a shorter one
        /// reuses them, so steady conversation allocates nothing per line.
        void EnsurePool()
        {
            if (_dmlAlloc == null) _dmlAlloc = new OrtAllocator(_step, _device);
            if (_pool == null)
            {
                _pool = new OrtMemoryAllocation[2][];
                _pool[0] = new OrtMemoryAllocation[_layers];
                _pool[1] = new OrtMemoryAllocation[_layers];
                _poolBytes = new long[_layers];
            }
            for (int i = 0; i < _layers; i++)
            {
                long elems = 1;
                for (int d = 0; d < _cacheDims[i].Length; d++)
                    elems *= d == _posAxis ? _prefillPos + Room : _cacheDims[i][d];
                long bytes = elems * sizeof(float);
                if (bytes <= _poolBytes[i]) continue;
                for (int h = 0; h < 2; h++)
                {
                    if (_pool[h][i] != null) _pool[h][i].Dispose();
                    _pool[h][i] = _dmlAlloc.Allocate((uint)bytes);
                }
                _poolBytes[i] = bytes;
            }
        }

        /// Layer `i`'s dims with the position axis at `pos` — a fresh array,
        /// because the binding may hold the one it was given.
        long[] DimsAt(int i, long pos)
        {
            var dims = (long[])_cacheDims[i].Clone();
            dims[_posAxis] = pos;
            return dims;
        }

        /// Collection to array, once per run. The interface only promises
        /// enumeration, and sixty-one values per step is a loop, not a cost.
        static void Fill(IDisposableReadOnlyCollection<OrtValue> from, OrtValue[] into)
        {
            int j = 0;
            foreach (var v in from)
            {
                if (j >= into.Length) break;
                into[j++] = v;
            }
            if (j != into.Length)
                throw new InvalidOperationException(
                    "the bound run returned " + j + " values, not " + into.Length);
        }

        /// The bound outputs come back in BINDING order, and everything above
        /// indexes on that. Asserted once per binding against the names the
        /// binding itself reports, because a silent transposition is layer
        /// 3's keys fed as layer 7's — wrong speech, no error.
        static void MustMatch(OrtIoBinding b, string[] cache)
        {
            var names = b.GetOutputNames();
            if (names.Length != cache.Length + 1 || names[0] != "logits")
                throw new InvalidOperationException(
                    "bound outputs are [" + string.Join(",", names)
                    + "], wanted logits first then " + cache.Length + " caches");
            for (int i = 0; i < cache.Length; i++)
                if (names[i + 1] != cache[i])
                    throw new InvalidOperationException(
                        "bound output " + (i + 1) + " is '" + names[i + 1]
                        + "', wanted '" + cache[i] + "'");
        }

        void BindArray(OrtIoBinding b, string name, VoiceConditionals.Array3 a)
        {
            if (a == null)
                throw new InvalidOperationException("the voice has no '" + name + "'");
            var shape = new long[a.Shape.Length];
            for (int i = 0; i < shape.Length; i++) shape[i] = a.Shape[i];
            OrtValue v = a.Floats != null
                ? OrtValue.CreateTensorValueFromMemory(a.Floats, shape)
                : OrtValue.CreateTensorValueFromMemory(a.Longs, shape);
            _lineInputs.Add(v);
            b.BindInput(name, v);
        }

        /// The bound twin of `Read`: the logits value is host memory by
        /// construction (bound to the CPU device above), and a short read is
        /// a failure for the same reason it is one there.
        bool ReadBound(OrtValue v, float[] logits)
        {
            var span = v.GetTensorDataAsSpan<float>();
            int n = Math.Min(logits.Length, span.Length);
            for (int k = 0; k < n; k++) logits[k] = span[k];
            if (n != logits.Length)
                Why = "the bound graph gave " + n + " odds, the sampler wants "
                      + logits.Length;
            return n == logits.Length;
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
            if (_bindPrefill != null) _bindPrefill.Dispose();
            if (_bindStep != null) _bindStep.Dispose();
            if (_tokVal != null) _tokVal.Dispose();
            if (_posVal != null) _posVal.Dispose();
            if (_logitsHome != null) _logitsHome.Dispose();
            if (_pool != null)
                for (int h = 0; h < 2; h++)
                    for (int i = 0; i < _layers; i++)
                        if (_pool[h][i] != null) _pool[h][i].Dispose();
            if (_dmlAlloc != null) _dmlAlloc.Dispose();
            if (_runOpts != null) _runOpts.Dispose();
            if (_device != null) _device.Dispose();
            if (_prefill != null) _prefill.Dispose();
            if (_step != null) _step.Dispose();
            if (_decode != null) _decode.Dispose();
        }
    }
}
#endif
