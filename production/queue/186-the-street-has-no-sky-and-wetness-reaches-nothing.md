line: art (the visual bar) and engine, jointly
spec: The Unreal probe binds a sky and a reflection source, and Wetness reaches the
  material. All three, because none of them works alone.
acceptance: a frame from cam_hook in which the road reflects something, judged by Jafar
  beside Codex's Hook sheet
max_sessions: 2
status: READY 2026-09-09, and it is RUNG 1's real obstacle. Found while measuring queue
  176, not by looking for it.
  CORRECTED 2026-09-09 09:55Z BEFORE ANY BUILD: "none-black" was a hardcoded printf
  and never a reading. The far field is the height fog's inscattering colour lifted to
  near white by auto-exposure, proven by channel order (day 249.5/250.0/250.5 with
  R<G<B against day fog 0.55/0.58/0.62; night 188.4/179.6/179.3 with R>G=B against
  night fog 0.06/0.05/0.05). THE STRUCTURAL CLAIM STANDS, there is no sky actor, but
  A SKY BEHIND AN OPAQUE FOG IS INVISIBLE, so the fog's max opacity must come down in
  the same change or the dispatch returns today's frame.
  ORIGINALLY MEASURED: skyModel=none-black/phase-C-owns-the-hdri and
  ambientModel=trilight-3-directional/not-a-captured-sky. The condition NAMES an HDRI,
  belfast_open_field_2k, that the Unreal probe never binds. There is no skylight, no
  reflection capture and no captured cubemap: three directional lights and fog.
  WETNESS IS PARSED AND READ BY NOTHING in this engine. Three hits across the whole
  ue-probe tree, all in VignetteSpec.h: the field at 246, its initialiser at 248, its
  parse at 434. No read anywhere. It is NOT dead project-wide:
  ledger/Assets/Scripts/Game/StreetVignetteHost.cs:715 calls AssetLibrary.SetWetness in
  Unity. It is dead in the engine that takes rung 1's frame.
  WHY THESE ARE ONE ITEM AND NOT THREE. Codex's panel is lit BY its sky and its lower
  half is mostly sky and buildings reflected in standing water. Wiring Wetness alone
  makes the road darker and smoother WITH NOTHING TO REFLECT, which is a black road
  rather than a wet one. A builder given only the wetness half would discover that the
  expensive way.
