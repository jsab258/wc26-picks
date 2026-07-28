# TTS benchmark

**One file. Download it, run it.**

    python ledger_tts_bench.py

Direct link:
https://raw.githubusercontent.com/jsab258/wc26-picks/claude/game-dev-ai-automation-2h67ix/tools/tts-benchmark/ledger_tts_bench.py

It checks what is installed, offers to pip-install what is missing,
generates the audio from real game lines, prints what to listen for, and
opens the output folder. Everything it needs — the lines, the voices, the
engine adapters, the listening guide — is inside that one file.

Flags, all optional: `--yes` (install without asking), `--engine kokoro`,
`--quick`, `--no-open`.

Optional, for the XTTS cloning test only: drop 6-10 seconds of clean speech
per voice into `refs/` as `lena.wav`, `rocco.wav`, `mara.wav`,
`crowd_m.wav`, `crowd_f.wav`. Any clean American-accented speech works.
