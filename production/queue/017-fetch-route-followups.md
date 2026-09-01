line: infrastructure (content pipeline)
spec: production/specs/vignette-fetch-01.json; the fetch-route report of 2026-09-01
acceptance: all three named below closed, each with the check that proves it
max_sessions: 1

Three findings from proving the fetch route, none blocking, all small.

1. `THIRD-PARTY.md` line 186 names `ledger/Assets/Decals/ambientcg/`. Those
   files moved to `StreamingAssets/Decals/ambientcg/` on 21 August in
   2266a962. A stale path inside a LICENCE document is worse than a stale
   path elsewhere: that file is the answer to "where did this come from",
   and it currently points at nothing.

2. `SURFACES` is duplicated in `tools/citypack/fetch_textures.py` and
   `tools/citypack/pack_check.py`, so adding a logical surface means editing
   two lists plus AssetLibrary. One idea, three implementations. This
   project has dedup'd the same shape twice in a week and found a third
   copy each time.

3. `tools/citypack/catalogue.json` carries `note: "complete"`. It is
   complete for ambientCG's MATERIAL type and says nothing about Decal,
   Atlas, 3DModel, Substance, HDRI or Terrain. Proof the gap is real:
   `AsphaltDamageSet001` is on disk here, came from ambientCG, and is not in
   that file. The note must say which type it covers, because "complete" is
   true of materials and reads as true of the library.
