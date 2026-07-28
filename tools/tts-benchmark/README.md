# TTS benchmark

**One file. Download it, run it.**

    python ledger_tts_bench.py

Direct link:
https://raw.githubusercontent.com/jsab258/wc26-picks/claude/game-dev-ai-automation-2h67ix/tools/tts-benchmark/ledger_tts_bench.py

It builds a **separate clean environment per engine**, installs what that
engine needs, generates audio from real game lines, prints what to listen
for, and opens the output folder.

Per-engine environments are the point: these packages pin conflicting torch
versions, and in the first rounds installing one silently broke the next.
Now an engine can only ever fail on its own terms, and the failure is printed
with a full traceback path at the end of the run.

## Engines

| engine | why it's here |
|---|---|
| `kokoro` | small, fast, American English — the bet that we can voice dialogue **live** |
| `chatterbox` | explicit **exaggeration** control + zero-shot cloning — the direct answer to piper's flat affect |
| `xtts` | voice **cloning** — if clones hold up, the pre-generated/live seam disappears |
| `piper` | the control case. **Already judged: too synthetic, no emphasis.** This is the floor |
| `eleven` | opt-in paid reference, to calibrate the ceiling. Never runs unless asked |

## Flags

All optional. `--engine kokoro` (or a comma list), `--yes`, `--quick`,
`--no-open`.

Only doing one? `--engine chatterbox` is the one that answers the open
question — whether an engine can take direction.

## Optional extras

- **Cloning test.** Drop 6–10 seconds of clean speech per voice into `refs/`
  as `lena.wav`, `rocco.wav`, `mara.wav`, `crowd_m.wav`, `crowd_f.wav`. Any
  clean American-accented speech works. Without it, `xtts` uses its built-in
  studio speakers and `chatterbox` its default voice — both still run.
- **Paid reference.** `set ELEVENLABS_API_KEY` then `--engine eleven`.
  The free tier covers this benchmark several times over. Nothing is bought
  and no account is created for you.

## Disk

Each engine venv is a few GB, mostly torch. `--engine <one>` if space is
tight. Everything the script creates (`.venv-*`, `models/`, `ledger-tts-out/`)
is gitignored and safe to delete.
