line: production (asset pipeline)
spec: game-design/decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md, Ruling 10
acceptance: a figures block placed in Unity; plates regenerated from canon's street-districts line; twenty G7 tags off the five canon names; every image under decals2d/ OPENED and the manifest's review line dated and specific
max_sessions: 2
status: READY 2026-09-02. content-wrangler first, then engine-specialist.

1. THE FIGURE. A `figures` block in `vignette-scene.json`: which held body,
   which idle clip, x, z, facing. Sizes come from the fbx manifest and are
   NEVER invented. Then the Unity placement through the existing character
   path. Without it the scene is not an admissible (b) scene, because D1b's
   mandatory contents name at least one clothed character body.

2. THE PLATES. `make_vignette_2d.py` line 289 takes `districts[0]`, so all
   three plates stamp `the Hook`. Canon now carries the map. Make the
   generator READ it and regenerate. The resident measured that a bare re-run
   does not fix this: the generator never reads the map, so the output is
   byte-different and district-identical.

3. THE TAGS. G7 is unblocked; canon carries TANNER, SNIDE, GULL, QUAY FIRM
   and PARADE RATS. Twenty tags off five names, marker and chrome variants,
   deterministic, because a tag must spell its crew.

4. OPEN THE IMAGES. Every file under `production/assets/vignette/decals2d/`
   gets looked at, and the manifest's `review` line changes from `pending` to
   a DATED SENTENCE NAMING WHAT WAS LOOKED AT. Three of eight were opened at
   generation; the rest are unread and the manifest currently says so
   honestly. Rule 4: open the artifact you are shipping.
