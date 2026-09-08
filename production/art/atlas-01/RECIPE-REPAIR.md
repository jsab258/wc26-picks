# Recipe repair, first continuation revision

The independent review supplied by the owner correctly found that the model hardcoded shell, stair, store and upper-room geometry while the upper plan and JSON could change independently.

`data/mickeys.json` now explicitly owns the shell and slab, stair start/run/landing/void, partition edges and apertures, upper windows, room-relative furniture, roof and annex dimensions. `scripts/pub_geometry.py` converts those decisions into geometry commands. Both the actual SVG plan renderer and the Blender adapter consume those commands. It is arithmetic over chosen objects, not a room solver. The original source bay, street and front door horizontal anchors remain untouched.

Minor plan/model discrepancies are corrected to the retained model design: the upstairs desk, kitchen counter and bath now appear in the plan; the till's 1.35 m overall top is represented as a 0.30 m object on a 1.05 m counter. Partition intersections follow explicit room edges. The upper shell is 6.20 m high in local coordinates, 6.30 m at the source datum. No new gameplay or building-code claim follows.

The retained headroom check now counts the actual treads beneath the actual front slab edge and subtracts the actual slab thickness. Result for this design: 2.1263 m, a limited rectangular arithmetic clearance. The old 2 m comparison is retained as a design check, not a regulatory threshold. Landing headroom, handrails, door poses, circulation and structural support remain untested. The private doorway is only 0.085 m from the first tread measured from the inner face of the 0.215 m front wall. Its swing conflict is illustrated in [access alternatives](previews/mickeys-access.png).

42 existing checks passed. Twelve focused mutation/source checks additionally move a room, widen a partition, change a stair going and alter the void/slab. They compare the actual SVG's projected rectangles against the commands consumed by the model adapter, and demonstrate detection of an intentionally stale drawing. They do not execute bpy, prove rendered mesh agreement or certify access.

Claude should consume the updated existing render-request.json, not create another commission or scheduler. The studio lane requires a wrapper at its conventional tools/art-recipes path, outside this art commission's write boundary, and must use the pinned source rather than whichever branch head has advanced. It also currently banks PNGs alone; the requested blend, input receipt and log need preserving through the studio's existing result path. No request was dispatched.
