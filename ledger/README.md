# LEDGER — Unity project

The game. Design documents live in `../game-design/`.

- Unity 6 (6000.0.x), HDRP. Open the `ledger/` folder in Unity Hub; packages restore
  automatically on first open (internet required, takes a few minutes).
- `Assets/Scripts/` — all game code (C#).
- `Assets/Scenes/` — M0 scene: `Block.unity` (one city block tech spike).
- API keys (LLM, TTS) are read from `Assets/StreamingAssets/secrets.json`, which is
  git-ignored. Copy `secrets.example.json` and fill in real keys locally / in CI secrets.

Current milestone: **M0 tech spike** — see `../game-design/m0-plan.md` for scope and
pass/fail tests.
