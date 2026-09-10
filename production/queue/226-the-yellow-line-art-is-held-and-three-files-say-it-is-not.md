line: art (the visual bar)
spec: The three places claiming no yellow road-line art is held are corrected,
  because the art is held, it is CC0, and it was measured.
acceptance: the three sentences corrected in place with nothing deleted, and
  the measurement quoted beside each
max_sessions: 1
status: READY 2026-09-09 22:05Z. A decayed claim, found while answering a
  different question, which is where they are always found.

  THE CLAIM. Three files say, in their own words, that no yellow line art is
  held here. It is FALSE and the refutation is a measurement rather than a
  sighting: ledger/Assets/StreamingAssets/Decals/ambientcg/
  RoadLines011_2K-PNG_Color.png is 2048x2048 of worn YELLOW paint, brightest
  one per cent at RGB 216/180/48, yellowness 150.5, against 3.3, -0.3, 4.7,
  4.6 and 4.8 for the other five RoadLines sets, which are white. CC0 1.0 and
  already recorded in that directory's THIRD-PARTY.md.

  CORRECTION, 2026-09-10: IT WAS FOUR SITES AND NOT THREE, and this item's own
  FILENAME still says three. The fourth is ledger/CoreTests/Program.cs, found by
  grepping the SENTENCE rather than the site, which is the rule this item was
  filed under and which the filing itself did not follow. A fifth copy sits in
  ledger/Assets/StreamingAssets/Vignette/scene.json and is deliberately NOT
  edited: it is a staged build product of tools/stage-vignette-scene.py, a
  second writer is how a file drifts, and that file is separately stale because
  it carries no C15 fascia entries at all. The name is left alone on purpose, so
  that the undercount stays visible in the index rather than being tidied away.

  THE THREE SITES, and the rule about copies is why all three are named:
    ledger/Assets/Scripts/Core/StreetVignette.cs:1409 to 1412
    production/specs/vignette-scene.json, the A5_double_yellow_lines note
    production/specs/vignette-bill-of-materials.json, that line's source field

  WHY IT IS FILED AND NOT FIXED TONIGHT. Two of the three files are being
  edited by a builder in this same session and an edit under it would be lost
  or would collide. The third is Core.

  WHAT IT DOES NOT LICENCE. It does not follow that the pack file should be
  used: paint_yellow is ProceduralOnly on the Unity side by AssetLibrary.cs
  1613, so binding a texture on one engine and a tint on the other diverges the
  two engines, which is the one thing D1 exists to avoid. THE CORRECTION IS TO
  THE SENTENCE, and whether to revisit ProceduralOnly on BOTH engines together
  is a separate question that belongs on the quality ladder.
