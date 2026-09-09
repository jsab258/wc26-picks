line: art (the visual bar) and engine, jointly
spec: A piece whose surface does not resolve to a pack file is PAINTED ANYWAY,
  by the three rules the Unity host already has and the UE probe does not.
acceptance: piecesUnpainted=0 over the pieces examined, with surfaceStatus
  printed as RESOLVED or PROCEDURAL per surface, and the rung-1 frame opened
  afterwards showing yellow kerb lines and lettered shop fascias
max_sessions: 2
status: READY 2026-09-09 21:15Z, REWRITTEN 22:05Z. THE FIRST VERSION OF THIS
  ITEM WAS WRONG IN ITS DIAGNOSIS AND IN ITS REMEDY, and the correction is the
  more useful half. It asked for four surfaces to be SOURCED. Nothing needs
  sourcing. Every one of the four is already answered by files or code in this
  repo, and two of the four are not texture-pack surfaces at all.

  WHAT card AND multiply ACTUALLY ARE. They are DECAL BLEND MODES, not
  surfaces. ledger/Assets/Scripts/Core/StreetVignette.cs:57 declares the
  overload in words, "FOR A DECAL IT IS THE BLEND, card or multiply ... a decal
  has no library surface", and line 1651 throws on any other value. The picture
  comes from the piece's own asset field. All twenty are on disk: ten generated
  PNGs under Decals/generated (the four fascias, three interiors, a gig bill
  and two notices) and five ambientCG sets at 2K under Decals/ambientcg
  (ManholeCover011, AsphaltDamageSet001, Leaking005, Moss001, Sticker001), CC0
  1.0 and recorded in that directory's THIRD-PARTY.md. decalImagesOnDisk=20/20
  over the 20 decal pieces examined, 0 missing. ASKING texRoot FOR card.png IS
  ASKING FOR A FILE THAT BY DESIGN CAN NEVER EXIST.

  WHAT paint_yellow IS. ledger/Assets/Scripts/Game/AssetLibrary.cs:1613 marks
  it ProceduralOnly, so a pack file for it is DELIBERATELY IGNORED and it
  renders from the SurfaceSpec tint, worn municipal yellow at 0.78/0.66/0.18.
  Dropping paint_yellow.jpg into the pack would make the two engines render one
  surface from different inputs, which is the single thing D1 exists to avoid.

  WHAT interior IS. No pack file, and Unity does not need one: it generates
  from a tint at 0.18/0.13/0.08 with emission 0.02 and BORROWS its normal and
  roughness from the window surface by an explicit rule at AssetLibrary.cs:611,
  mapsFrom = logical == Interior ? Window : logical. It is the one of the four
  where a pack file would be legitimate, and it is still not required.

  THE ACTUAL CAUSE OF THE BLANK FRAME, and it is one line.
  ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp:2749:
      if (Idx < 0 || GBinds[(size_t)Idx].Status != "RESOLVED") { continue; }
  A PIECE WHOSE SURFACE DID NOT RESOLVE GETS NO MATERIAL INSTANCE AT ALL and
  renders the engine default. That is 10 card + 10 multiply + 6 interior + 4
  paint_yellow = 30 pieces, and 593 minus 563 is 30, so the arithmetic closes
  exactly. It is why the yellow lines, the fascia signs, the shop interiors and
  the grime are all absent from the frame that rung 1 is judged on.

  THE UE PROBE IS MISSING FOUR RULES THE UNITY HOST HAS AND THAT ARE ALREADY
  WRITTEN DOWN: the SurfaceSpec tint fallback, the interior-borrows-window map
  rule, any decal texture path at all (the emitter's own comment at line 870
  says "A DECAL IS A QUAD UNTIL PHASE C"), and the _b variant rule at
  AssetLibrary.MaterialVariant:271, whose absence is why 15 of the 51 staged
  pack files are named by nothing on the UE side.

  THE RESOLVER WAS SIMULATED RATHER THAN ASSUMED. Its rule is SurfaceBind.h:44
  to 84, candidates <surface> x {"","_n","_r"} x {.png,.jpg,.jpeg}, first hit
  wins. Re-implemented in Python against the 51 files on disk it printed
  surfacesResolved=12/16 mapsFound=36/48
  surfacesAbsent=card/interior/multiply/paint_yellow, character for character
  what the PC printed. The ruler is understood, so these readings are about the
  pack and not about the instrument.
