# License allowlist (law; verify weights license, not code license; recheck at ship)

SHIP-SAFE
1. Voices: the local voice pipeline as built; Kokoro (Apache 2.0), Chatterbox (MIT, keep watermark), Piper (MIT original; the active fork is GPL-3.0, acceptable for generated audio, check before embedding code). ElevenLabs on paid tiers if adopted.
2. 3D: TRELLIS/TRELLIS 2 (MIT). Meshy or Tripo paid tiers only. CC0 libraries (Poly Haven, ambientCG, Sketchfab CC0 filter). Fab purchases under the Fab Standard License. Objaverse only with per-object license filtering.
3. Characters: MetaHuman (free under 1M revenue, usable outside Unreal, never to train or enhance AI models). Character Creator 4 exports per Reallusion EULA. Mixamo animations.
4. Faces: Audio2Face-3D (MIT).
5. Music: self-hosted MusicGen (MIT) or Stable Audio Open; ElevenLabs Music if adopted. Final pick re-verified when radio production starts (open-questions 4).
6. Geodata: OSM/Overture as skeleton only, geometry self-generated, OSM attribution shipped, layouts fictionalized.

NEVER SHIP
1. XTTS-v2 or F5-TTS official weights output (non-commercial).
2. Luma Genie outputs.
3. Hunyuan3D outputs if distribution may include EU, UK or South Korea (territory-excluded license); given Switzerland plus likely EU reach, treat as banned.
4. Google Photorealistic 3D Tiles as shipped assets.
5. Real brands, logos, car models, lyrics, likenesses, cloned real voices, celebrity styles.
6. Suno or Udio output until their legal posture is re-verified at ship (Suno lost in Munich 2026-07-31, not final).

PROCESS
1. Every asset and generated output carries a license tag; untagged fails the license gate.
2. New tool adoption requires a decision record citing the weights license.
3. At ship-prep: Steam generative-AI disclosure for player-facing content (coding tools exempt); FTC rule: never market AI-made as human-made.
