# Live speech at conversational latency — analysis and experiment plan

> **STATUS — SPEC**, written 2026-08-12. No code changes yet; this is the
> thinking Jafar asked for before anything gets built. The measurements it
> rests on are in `voice-live/speed-report.txt` and `shape-report.txt`, all
> taken 11–12 August on the machine that will run the game.

## 1. Reframe: the number that matters is time-to-first-sound

Everything measured so far answers "how long until the WHOLE line is ready":
5.9s for a 3.4s sentence. That is the wrong question for feel. A player does
not need the whole line; they need the character to START talking, and to not
stop once started. Every real-time TTS system works this way.

So the target splits in two:

- **Latency**: time from "reply text exists" to the first audible sample.
  Target under ~1.2s, which with an acknowledgment beat (the character turns,
  breathes, taps the bar) reads as a person deciding to answer.
- **Sustainability**: once audio starts, tokens must be generated at least as
  fast as playback consumes them, or the voice stutters mid-line.

## 2. The arithmetic that governs both

The model emits acoustic tokens at exactly **25 per second of audio** (86
tokens → 3.44s). Playback therefore consumes 25 tok/s.

Generation today: 42ms/step median → **23.8 tok/s. Just below break-even.**
Streaming built today would underrun mid-line. This is the single fact that
orders the whole plan: **the step rate must rise before streaming is worth
building, and every step-rate gain multiplies through everything.**

Decode at 4 solver steps runs at ~2.1x real time on the card, so chunked
decode can keep up — but it shares the card with the step loop, so the margin
must survive contention. Unmeasured; experiment 1 covers it.

## 3. Streaming is designed into the model we already ship

Read from the installed package, not guessed:

- `flow.inference(finalize=False)` drops the last `pre_lookahead_len (3) ×
  token_mel_ratio (2)` mel frames — a chunk renders with a 3-token lookahead
  and the boundary is re-rendered correctly by the next chunk. Chunked
  synthesis is a first-class mode, not a hack.
- `HiFTGenerator.inference(cache_source=...)` exists "to avoid glitch": the
  vocoder's noise source is carried across chunks so seams are continuous.
  Our export already externalised that noise, which is the hard half done.
- The docstring says "Please use `S3GenStreamer` for streaming synthesis" —
  upstream CosyVoice lineage streams in production.

Cost caveat: each chunk re-encodes prompt + all tokens so far and slices off
the new mels, so per-chunk cost grows along the line. At 4 solver steps and a
trimmed prompt this looks affordable for lines up to ~15s; experiment 5
measures it rather than trusting this sentence.

## 4. Where the 42ms per step actually goes — the untested hypothesis

The transformer is 30 layers, 16 heads, 64-dim (config read from the
package). The KV cache at a mid-sentence position is ~60 tensors × ~1.2MB ≈
**74MB — and the loop currently downloads all of it to CPU and re-uploads it
every step**, because ONNX Runtime feeds/outputs are host memory unless bound
to the device. ~150MB of PCIe traffic per 42ms step could plausibly be half
the step.

Two zero-quality-risk fixes if the hypothesis holds:

- **Keep the cache on the GPU** (OrtIoBinding in C#; onnxruntime-genai exists
  precisely for DML LLM decode loops with in-place KV buffers).
- **fp16 — FIRST NUMBERS (12 Aug): steps 42→31ms, and sustainability is
  CROSSED.** 32.3 tok/s against the 25 playback needs, from the conversion
  alone, before residency. Session opens halve too (2.5s/1.8s). Follow-up
  run settled steps at **26ms — 38 tok/s, 1.5x margin.** The prefill's
  apparent 0.30→1.06s regression was ONE-TIME KERNEL WARM-UP: the second run
  in the same session measures **0.08s, four times faster than fp32** — the
  game pays the warm-up once at load with a throwaway prefill. A warmed line:
  0.08 + 74 steps at 26ms + decode = 4.4s of work for 3.0s of speech;
  time-to-first-sound if streamed today ~1.3–1.7s. Remaining asterisk: the
  fp16 graphs REFUSE to load on the CPU EP (an optimizer-fusion bug on the
  converted graph), so CPU-only machines stay on fp32, which costs nothing:
  at 68-77ms per CPU step they were never speaking live anyway. The wav is
  with Jafar; ears close the lever.
- **LEVER B CLOSED (12 Aug, by rate): the conversion corrupts the sampling
  distribution.** Ten seeds of the same nine-word line: fp32 gives a tight
  80–110 tokens, zero early stops. fp16 gives **4, 0, 170, 0, 97, 233, 222,
  214, 0, 18** — four-in-ten die before fifteen tokens, THREE at zero, and
  the survivors bloat to 2–2.5x length. That is not near-tie noise; the odds
  landscape itself is distorted. The tiny-model agreement (0.0%) did not
  transfer to 30 layers of accumulation. The speed was real (26ms steps,
  0.08s warmed prefill) and is worthless on a distribution that flips a coin
  between saying nothing and rambling. Salvage would be mixed precision —
  fp32 layernorms/head via block lists — shelved unscheduled beside the
  binding probe and the one-row export. **The streaming margin now rests on
  residency (lever A) over fp32 graphs**, and the worker design gains a
  no-underrun rule that needs no margin at all: begin playback when
  remaining-work < remaining-audio (a head-start stream), which puts first
  sound at (total work − audio length) ≈ 1.0–1.4s once residency lands.
- **And the sweep bought a guard (12 Aug): the stop-token floor now scales
  with the words.** The 4-token render of the nine-word line (nine COUNTED
  — it spent a day quoted as "twelve-word" off a comment) would have
  PASSED the game's old constant floor of four steps — played as a fifth of
  a second of noise, then taught the latency estimator that nine words cost
  five steps. `Core/SpeechLoop` now refuses a stop under 3 steps/word
  (broken renders measured ≤2/word, healthy ≥9/word, so it sits in the gap
  nearer the broken edge; "No." at 19 tokens clears its floor of four
  untouched). Refused lines get their own verdict reason
  (`StoppedShort`, not `StepCeiling` — opposite fixes) and are excluded from
  the whole-line estimator fold. Refusal, not stop-suppression: the same
  sweep shows what lies past a forced continue — the fp16 seeds that did not
  stop early rambled to 170–233 tokens. The sweep tool now prints the same
  per-word floor instead of its old flat <15, which had read the 18-token
  render as healthy.
- **fp16 rationale, kept for the record**: the shipped weights are bfloat16 upstream — we exported at fp32,
  DOUBLING the bandwidth the model was trained to need. Halves both transfer
  and compute on a bandwidth-bound decode.

**Lever A, first two live rounds (12 Aug): the path ACTIVATES, and the
allocator is the enemy.** The C# binding ran resident on the RX 6700 —
prefill and step one — and step two died both times in layer 0's cache
Concat ({Application Error}), identically with and without the API's
synchronize calls. The signature: step one consumes the PREFILL session's
buffers and works; step two consumes the step session's OWN pool-allocated
outputs and dies. Reading: DirectML's internal allocator recycles a run's
output buffers as the next run's scratch, live references or not. Two
findings worth the rounds on their own: the python preview's access
violation does NOT reproduce through the C# binding — the failure is a
catchable managed exception, so the in-game fallback works and the attempt
is safe to ship — and the bench's refuse-then-time design caught it before
any wrong number existed. Round three in flight: the cache ping-pongs
between two explicitly-owned max-size device blocks (exact shape bound over
each per step), so the allocator's pool never touches it — the same shape
onnxruntime-genai uses. If that still fails, the fallback plan is the
static-length KV export: scatter instead of concat, shapes that never grow,
which also makes each step O(1) instead of O(line).

**Measured 12 Aug (experiment 1, safe half): the slope is real.** On the
RX 6700: pos10 34.5ms, pos100 45.1ms, pos200 59.3ms, pos400 89.5ms —
**31.8ms flat + 142us per position.** The arithmetic closes: each position
adds ~2MB of cache round-trip, and 142us/2MB is ~14GB/s, which is PCIe, not
compute (the attention maths at these lengths is negligible). So at a
mid-line position roughly a third to a half of every step is shipping the
cache, rising as the line grows — residency is confirmed worth building, and
should take a position-100 step from ~45ms to ~21ms before fp16 touches the
rest. One caveat for every number from this machine: the card also carries a
Parsec virtual display, so an encoder shares it whenever Jafar is connected.

The dev machine has an **AMD GPU** — Jafar has said so twice and it is
recorded here so it stops being re-asked — and the game must ship for AMD
and NVIDIA both. That settles the provider question rather than opening it:
DirectML is not a fallback, it is the shipping baseline, the one
vendor-neutral GPU path on Windows. CUDA is not a lever for this machine and
at most an optional NVIDIA fast path much later. Everything above — cache
residency (onnxruntime-genai's DML backend runs on both vendors), fp16 —
is vendor-neutral. The probe still reports the adapter name, for the record
of which AMD card these numbers describe.

## 5. A correction: "guidance is not removable" was concluded from a confounded experiment

The no-guidance test ran Ada to the 1001-token ceiling and I declared
guidance essential. But the crude sampler in `time-a-line`/`speak-a-few` has
**no repetition penalty** — and every real sampler in the package (both
`inference` and the no-CFG `inference_turbo`) applies repetition_penalty 1.2.
Runaway generation is the textbook symptom of a missing repetition penalty.
Upstream ships `inference_turbo` — single-row, no guidance — as a supported
path, which they would not if the model could not stop without CFG.

So the experiment conflated two variables, and the fair retest (12 Aug)
confirmed it: with the penalty in the sampler, five of five lines spoke, Ada
stayed in her normal token range, and the runaway never recurred. The
confounding is proven.

**And then lever C died anyway, for a better-measured reason.** Per-step cost
halves without guidance (42→28ms) — but the model generates MORE tokens for
the same words, and the inflation lands hardest exactly where the game lives:
the one-word line "No." took 19 tokens guided (0.8s of audio) and 46 tokens
unguided (1.8s, heard blind by Jafar as "slowed/stretched"). End to end the
wall-clock win measured 0–20% per line, not 50% — on the shortest line the
unguided version was SLOWER to make — and the drawn-out delivery is a real
quality cost on the interjections that dominate street dialogue. Guidance
STAYS. The streaming margin therefore rests on levers A and B alone: ~20ms
guided steps → ~50 tok/s against 25 needed, which still clears the
interleaved budget.

## 6. The levers, ranked

| # | lever | expected | quality risk | decided by |
|---|---|---|---|---|
| A | KV cache stays on GPU | 1.5–2x steps | none | position-slope probe, then IOBinding probe |
| B | fp16 text graphs | up to 2x steps, composes with A | near-zero (weights are bf16-native) | sampler agreement + listen |
| C | no-guidance, retested fairly | 1.5x steps, composes | real — needs the five-line listen | rep-penalty retest |
| D | streaming (chunked flow + seam cache) | whole-line wait → ~1s to first sound | seam audibility | two-chunk vs one-shot diff + listen |
| E | prompt trim 250→50 tokens | ~0.3s per decode/chunk | voice similarity | listen |
| F | design cover: instant text, typewriter, reaction beat, LLM sentence-pipelining | perceived latency | none | play it |

Not on the list: anything needing training (CFG distillation, smaller model),
swapping the TTS model, and further solver-step cuts (4 is already approved
by ear; 2 would need re-listening for marginal gain).

## 7. The leg nobody has measured

The reply TEXT comes from a network call before any of this starts, and it
has never been timed. It streams, so the fix is pipelining — speech starts on
the first sentence while the rest still arrives — but the budget needs the
number. Measure time-to-first-sentence and time-to-done for a typical
in-character reply, from the container and from the game.

## 8. Composite budgets (86-token sentence, first-chunk = 28 tokens)

| state | first sound | sustained tok/s vs 25 needed |
|---|---|---|
| today, if streamed | ~2.2s | 23.8 — **underruns** |
| A or B lands (steps ~20ms) | ~1.2s | ~50 |
| A+B+C land (steps ~12ms) | ~0.9s | ~80 |

Plus design cover on top: text is instant in all cases, and the reaction beat
absorbs most of the first second. That is "close to real time" territory —
not by making the model faster than physics, but by not waiting for work that
has not happened yet.

**Experiment 1 outcomes (12 Aug), all four questions answered:** the card is
an RX 6700 sharing with a Parsec display encoder. The slope is confirmed (see
section 4): residency is worth ~2x on steps and gets built in C#. The python
io-binding preview is CLOSED — 0xC0000005 inside the DML build's device
allocation, which also explains the first combined run's silent hour. And
CONTENTION IS CLOSED THE HARD WAY: running the step session and the decode
session concurrently from two threads crashes the process with the same
access violation, on a stack where running them SEQUENTIALLY in one process
has worked hundreds of times. So the streaming design is settled by a crash
rather than a benchmark: **one thread, strictly interleaved — N steps, then a
chunk decode, never overlapped.** The sustainability arithmetic must carry
the decode pauses: per 25-token chunk, 25 steps PLUS one chunk decode must
fit in the second of audio the chunk buys. At today's speeds that is ~1.9s
per 1.0s — underruns; at residency+fp16 speeds (~15ms steps, ~0.5s chunk)
it is ~0.9s per 1.0s — sustainable, with the step-rate work carrying
slightly more of the load than the pre-crash budget assumed.

## 9. Experiment order (cheapest information first, all via the watcher)

1. **probe-step-costs** — step time vs position, GPU name, step-vs-decode
   contention. Decides A's premise and streaming's margin. No new graphs.
2. **rep-penalty retest of no-guidance** — five lines, three voices, one wav.
   Decides C.
3. **fp16 export + selftests** — agreement numbers here, listen there.
   Decides B.
4. **IOBinding / GenAI spike** — the engineering half of A, C# side.
5. **chunk-seam test** — same tokens one-shot vs two chunks with lookahead +
   `cache_source`, numerical diff then ears. Decides D's quality.
6. **LLM leg timing** — decides how much F matters.

Then, and only then: build the streaming worker into `Audio` with chunked
delivery, and re-derive `PatienceSeconds` as a time-to-first-sound bound
instead of a whole-line bound.
