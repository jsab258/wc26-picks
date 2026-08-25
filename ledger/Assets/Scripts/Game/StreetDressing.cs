using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// THE STREET HAD NOTHING STANDING ON IT (kit-survey.md, M17.10).
    ///
    /// `tools/prop-reach` read `city-kit-roads` 45 unused and
    /// `city-kit-suburban` 13 unused — 58 models already on disk, already
    /// attributed (CC0 1.0, Kenney), that no line of the Game layer named.
    /// `game-design/agent-reports/kit-survey.md` measured every one of them
    /// from its own FBX vertex data and ordered 19 placed. This file is the
    /// second wave of that order: municipal planters, yard boundaries and
    /// roadworks. `Furniture` did the base-mesh vocabulary (bins, bollards,
    /// benches, double yellows) and this is its sibling on the two city kits
    /// — same phase, same deterministic rolls, same prop pipeline.
    ///
    /// WHAT IS NOT HERE, so an absence cannot read as a finding: MOST of the
    /// SIGNAGE half of the survey's order is still unbuilt — `road-sign-empty`,
    /// `road-sign-empty-hanging` and `road-sign-object-warning` — so
    /// `sign_post` and `sign_plate_warning` print `nothing-offered` every run
    /// until somebody wires them, which is the honest reading and the reason
    /// the catalogue names families nobody has called yet.
    ///
    /// THIS PARAGRAPH USED TO NAME `road-sign-object-street` AND
    /// `sign_plate_name` IN THAT LIST AND THAT IS NO LONGER TRUE. The street
    /// nameplates are built, in `StreetFurniture.NamePlate`, which stands the
    /// blade through THIS file's `Stand` — the reason `Stand` is `internal`
    /// rather than private. `sign_plate_name` therefore prints real numbers
    /// now, and a reader who trusted this list would have gone looking for an
    /// unwired family that is wired.
    ///
    /// SCALE IS MEASURED, NEVER ASSUMED. These FBX are not in metres — the
    /// survey derived 1 unit ~ 0.074 m from two independent call sites rather
    /// than assuming a convention — and the Unity import scale on top of that
    /// is unknown here, because the Game layer does not compile in this
    /// container. So `Stand` does what `MakeLamp` does: instantiate, gather
    /// every renderer, encapsulate the bounds, and normalise by the model's
    /// own measured world HEIGHT to its known true height in metres. The
    /// proportions of these models are correct; only the unit is in doubt, so
    /// one uniform factor from the height gets every other axis right for
    /// free. That is what makes a 12.40m fence run 12.40m without anybody
    /// hardcoding a scale factor that a re-import would falsify.
    ///
    /// THE TRUE HEIGHTS, from `tools/prop-dimensions.py` over each file's own
    /// vertex data (units x 0.074): cone 0.69, works barrier 0.96, works lamp
    /// 1.73, planter 1.31, every fence 2.00.
    ///
    /// EVERY SITE AND EVERY OUTCOME IS FILED WITH `Ledger.Core.KitDressing`.
    /// Rule 6 — built is not running — and the survey names the exact failure
    /// mode: a missing prop returns null and the site simply places nothing,
    /// which from ten metres is indistinguishable from a site that was never
    /// offered. `city_kit_*_bench` missed for a week that way. `Offered` at
    /// every site, and exactly one of `Placed`/`Missed`/`Refused` at every
    /// outcome.
    ///
    /// THE THIRD OUTCOME IS THE ONE THIS FILE GOT WRONG. The paragraph here
    /// used to say the geometry refusals were "the difference between" placed
    /// and offered, "named by `Flagged` so the refusal has a reason and not
    /// just a gap" — and that is exactly what it was, a gap. The five refusal
    /// sites below filed a reason and NO OUTCOME, so seventy-two sites in a
    /// realistic run sat in a bucket `kitPlaced` did not name: it printed
    /// `243/320/5`, where `missed=5` reads as a prop path that never fails
    /// beside an offered count 30% above placed, which reads as a prop path
    /// that fails constantly (`agent-reports/kit-dressing-audit.md` C2).
    /// `KitDressing.Refused(family, reason)` files the outcome and the reason
    /// in ONE call, so no site here can record why it was refused without
    /// being counted as refused.
    ///
    /// NO FALLBACK PRIMITIVES, DELIBERATELY. Every other placer in this file's
    /// family falls through to a tinted box on a miss. That was right when the
    /// box was the only thing there; it is wrong now, because a grey box at
    /// the right size is precisely what makes a miss invisible, and `Missed`
    /// is a better answer than a decoy. A run with no city-kit prefabs draws
    /// nothing here and says so on the done line.
    public static class StreetDressing
    {
        /// THE TALLY IS `WorldBuilder.KitTally`, AND THERE IS EXACTLY ONE IN
        /// THE PROJECT. This file's first draft declared its own instance and
        /// filed every count into it — which would have printed a populated
        /// `kitDressing=` on the done line, carrying the lamp path's real
        /// numbers, while every family here read `nothing-offered`. That word
        /// means "no call was ever made", so the verdict would have stated
        /// confidently that this pass never ran, at the exact moment it was
        /// running correctly. One idea, two implementations, and the one
        /// nobody looks at is the one missing a line — except here the second
        /// one does not go quiet, it answers wrongly.
        ///
        /// `SimDirector`'s done line prints `WorldBuilder.KitTally.Line()` and
        /// nothing else, so that object is the instrument; `MakeLamp` and
        /// `TrafficHost`'s secondary head already file into it.

        /// ---- densities, and where every one of them came from ------------
        ///
        /// Rule 2: no number here is a guess about how many objects "feel
        /// right". Each is a probability against a MEASURED census of the
        /// street graph, taken by compiling `Core/StreetMap.cs` on its own and
        /// printing it (25 Aug):
        ///
        ///     junctions           97
        ///     driveable edges    154, of which 112 are 30m or longer
        ///     blocks              52
        ///     block width        35.0 / 47.9 / 65.1  (min / median / max)
        ///     block depth        15.0 / 21.9 / 31.1
        ///     driveable edges by district — Hook 48, Copper Row 23,
        ///       Ironside 18, the Exchange 18, the Parade 23, Fairview 12,
        ///       Gullwing 12
        ///
        /// The survey asked for 6-10 roadworks clusters and 15-25 planters.
        /// The products below land at ~9 and ~20 against that census. They
        /// are the FIRST landed values and the done line is what settles
        /// them: `worksClusters` and `plantersPlaced` both ship their own
        /// denominator, so a run that offered forty sites and placed two
        /// cannot read like a run that offered two.

        /// Roadworks are a MARKET AND DOCKS thing here: Copper Row is the
        /// market quarter whose closed lane the survey names, and Ironside is
        /// the goods yards. 13 long Copper Row edges + 18 Ironside at 0.18 is
        /// ~5.6; the other 81 long edges at 0.04 is ~3.2; ~8.8 clusters.
        const double WorksShareBusy = 0.18, WorksShareElse = 0.04;

        /// Planters went into pedestrianised British high streets through the
        /// eighties, and they double as vehicle barriers. Copper Row (23
        /// driveable edges) and the Exchange (18) at one in two is ~20.
        const double PlanterShare = 0.50;

        /// One fence RUN SLOT per tile of a block's yard centre line, on every
        /// block whose yard the probe can find. 52 blocks, most of them
        /// yielding two or three runs, lands near the survey's 90-140 across
        /// all four variants.
        const double FenceShare = 0.80;

        /// THE YARD DEPTH THAT DECIDES WHICH FENCE MODEL IS EVEN LEGAL, and
        /// the number that reverses one of the survey's readings.
        ///
        /// The survey calls `fence-1x2`, `-1x3` and `-1x4` "straight runs" of
        /// 6.47 / 9.44 / 12.40m. They are NOT straight. Their own bounds say
        /// so and the vertex dump confirms it: each is 43.75 units (3.24m)
        /// DEEP, because the model is a U — a long back run with a 2.96m
        /// RETURN panel at each end. The single `fence` is the only straight
        /// panel in the kit (3.52 x 2.00 x 0.56m).
        ///
        /// That makes the U the better object, not the worse one: three sides
        /// of a terrace back yard is exactly what it is for. But it needs
        /// 2.96m of yard to stand in, and the yards here are not all that
        /// deep. `TerraceBlock` caps each row at `(blockDepth - 3) / 2`, so a
        /// block with a 15.0m depth leaves a 3.0m gap between the two terrace
        /// backs and a 31.1m one leaves 7-13m. Measured against the block
        /// census above that splits the city cleanly: the Hook, Copper Row,
        /// the Parade and the Exchange get ~3.0-3.9m (a back ALLEY, and the
        /// straight panel is the right object), Fairview, Gullwing and
        /// Ironside get 6.5-13.1m (a YARD, and the U drops in).
        ///
        /// NOT HARDCODED FROM THAT ARITHMETIC. The depth is PROBED off the
        /// built masses every run, because the arithmetic above is a reading
        /// of `TerraceBlock` and the buildings are the thing that is actually
        /// there — eight blocks once hung over open sea because a placement
        /// measured its distance to a datum without asking whether the datum
        /// existed under the footprint. `YardOf` asks.
        const float ReturnDepth = 2.96f;
        /// The U needs its returns plus a working clearance at each face.
        const float DeepYard = ReturnDepth + 1.25f;

        // ---- the pass ------------------------------------------------------

        /// One dressing pass over the finished street graph. Called from
        /// `WorldBuilder.BuildBlock` after the buildings exist, because every
        /// site here is found by probing the built masses rather than by
        /// recomputing where they were meant to go.
        public static void Build()
        {
            if (!WorldBuilder.TownPlanEnabled) return;
            var parent = new GameObject("StreetDressing").transform;
            Planters(parent);
            YardFences(parent);
            Roadworks(parent);
        }

        // ---- 1. municipal planters ----------------------------------------

        /// THE ONLY GREENERY IN A GREY TOWN, and bang on period: British town
        /// centres pedestrianised through the eighties and filled them with
        /// exactly this — a 2.96 x 2.22m concrete tub, 1.31m tall, doing duty
        /// as a vehicle barrier. Market street (Copper Row) and the Exchange
        /// forecourt, which is where the survey put them and where the two
        /// pedestrian-scale districts are.
        ///
        /// ON THE PAVEMENT BAND, measured rather than eyeballed: the kerb is
        /// at half the carriageway and the building line is `BlockSetback`
        /// (2.6m) behind it, so a tub centred 1.3m out from the kerb spans
        /// 0.19m to 2.41m of a 2.6m pavement and clears both.
        static void Planters(Transform parent)
        {
            foreach (var e in StreetMap.Edges)
            {
                if (!e.Driveable) continue;
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                var district = StreetMap.DistrictAt(a.X, a.Z);
                if (district != "Copper Row" && district != "the Exchange") continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 16) continue;
                dx /= len; dz /= len;
                var across = new Vector3((float)-dz, 0, (float)dx);

                // Two per long edge, at the thirds, so a wide forecourt gets a
                // pair rather than one lonely tub in the middle.
                for (double frac = 0.33; frac < 0.7; frac += 0.34)
                {
                    double x = a.X + dx * len * frac, z = a.Z + dz * len * frac;
                    if (Dressing.Roll(x, z, 71) > PlanterShare) continue;
                    int side = Dressing.Roll(x, z, 72) < 0.5 ? -1 : 1;
                    var at = new Vector3((float)x, 0, (float)z)
                             + across * (((float)e.Width * 0.5f + 1.3f) * side);

                    WorldBuilder.KitTally.Offered("planter");
                    // BOTH HALVES OF THE PLACEMENT. Distance to the pavement
                    // datum is the easy half; whether there is pavement under
                    // the footprint at all is the half that catches the fault.
                    if (StreetMap.OnRoad(at.x, at.z, 0.6))
                    { WorldBuilder.KitTally.Refused("planter", "in_road"); continue; }
                    if (!WorldBuilder.PointClear(at, 0.5f))
                    { WorldBuilder.KitTally.Refused("planter", "no_room"); continue; }

                    // Long axis along the street: the model's 2.96m span is
                    // its local x, and LookRotation puts local +z on `across`,
                    // which leaves local x lying along the kerb.
                    var go = Stand("planter", "", "city_kit_suburban_planter", at,
                                   Quaternion.LookRotation(across), 1.31f, PlanterConcrete, parent);
                    // THE HEIGHT THAT ACTUALLY LANDED, and it used to be
                    // `2.96f * 2.22f` — the tub's catalogue footprint in square
                    // metres, which the compiler folds to one literal. Sixteen
                    // planters filed sixteen copies of it and the spread printed
                    // `6.57..6.57..6.57`, the strongest-looking evidence on the
                    // line and the only cell on it that could not have
                    // disagreed with itself (audit C4). A constant is not a
                    // measurement.
                    //
                    // THE HEIGHT IS THE QUESTION `Stand` CAN ANSWER WRONGLY:
                    // its normalisation is skipped for a mesh under 0.01m tall,
                    // exactly as `MakeLamp`'s is skipped under 0.5m, and that
                    // is the one step here that can silently do nothing. Sixteen
                    // readings at 1.31 is then a true statement about sixteen
                    // objects, and one at 0.07 is the fault visible.
                    Bounds stood;
                    if (go != null && WorldBounds(go, out stood))
                        WorldBuilder.KitTally.Measured("planter", stood.size.y);
                }
            }
        }

        /// Weathered precast, one notch above the road surface and well under
        /// the 0.60 the bright-pixel instrument calls a bright pixel — the
        /// same reasoning as `Furniture.FurniturePaint`, which exists because
        /// an untextured mesh ships at albedo 1.00 and reads as a white box.
        static readonly Color PlanterConcrete = new Color(0.48f, 0.47f, 0.44f);

        // ---- 2. yard fences ------------------------------------------------

        /// THE ALLEYS HAVE NOTHING BEHIND THEM. Every block is a perimeter of
        /// terraces around an empty middle, and every alley mouth in the city
        /// looks into bare ground. A 2.00m solid boundary is the object that
        /// fixes it — at that height it is a yard wall or a builder's
        /// hoarding rather than a picket, which is what makes it neutral on
        /// both period and country.
        ///
        /// ONE RUN PER TILE of the yard's centre line, laid along the block's
        /// LONG axis, with the model chosen by the yard depth the probe found.
        static void YardFences(Transform parent)
        {
            foreach (var block in StreetMap.Blocks)
            {
                // The long axis: every block in this city is wider than it is
                // deep (35.0-65.1 against 15.0-31.1), so this is x for all 52
                // today — asked rather than assumed, because the block table
                // is generated and a future district need not obey it.
                bool alongX = block.Width >= block.Depth;
                double runSpan = alongX ? block.Width : block.Depth;

                float yard, mid;
                if (!YardOf(block, alongX, out yard, out mid)) continue;

                // Which model can legally stand in a yard this deep is
                // `PickFence`'s call; the axis and yaw are the block's.
                var dir = alongX ? new Vector3(1, 0, 0) : new Vector3(0, 0, 1);
                float yaw = alongX ? 0f : -90f;

                // Tile from one end, leaving the corner rows their depth. 6m
                // is the shallowest terrace row `RowDepth` can produce on this
                // map, so it is the margin that cannot cut into one.
                double t = 6.0;
                while (t < runSpan - 6.0)
                {
                    double remain = runSpan - 6.0 - t;
                    string v = PickFence(yard, remain);
                    if (v == null) break;
                    float runM = FenceMetres(v);

                    double c = (alongX ? block.MinX : block.MinZ) + t + runM * 0.5;
                    var at = alongX ? new Vector3((float)c, 0, mid)
                                    : new Vector3(mid, 0, (float)c);
                    t += runM + 0.6;

                    if (Dressing.Roll(at.x, at.z, 73) > FenceShare) continue;

                    WorldBuilder.KitTally.Offered("yard_fence");
                    // The datum-exists half again: a run whose ends are inside
                    // a terrace is a wall built through a house.
                    var endA = at - dir * (runM * 0.5f - 0.2f);
                    var endB = at + dir * (runM * 0.5f - 0.2f);
                    if (!WorldBuilder.PointClear(at, 0.1f)
                        || !WorldBuilder.PointClear(endA, 0.1f)
                        || !WorldBuilder.PointClear(endB, 0.1f))
                    { WorldBuilder.KitTally.Refused("yard_fence", "in_terrace"); continue; }

                    var go = Stand("yard_fence", v, "city_kit_suburban_" + FenceStem(v), at,
                                   Quaternion.Euler(0, yaw, 0), 2.00f,
                                   WorldBuilder.FurnitureWood, parent);
                    // METRES OF RUN, not a count: a run count alone cannot
                    // tell one 12.40m run from twelve 3.52m ones, which is the
                    // distinction the survey asked for by name.
                    if (go != null) WorldBuilder.KitTally.Measured("yard_fence", runM);
                }
            }
        }

        /// The deepest fence that fits both the yard and the run left. Null
        /// when nothing fits, which ends the tiling for that block.
        static string PickFence(float yard, double remain)
        {
            if (yard >= DeepYard)
            {
                if (remain >= 12.40) return "1x4";
                if (remain >= 9.44) return "1x3";
                if (remain >= 6.47) return "1x2";
            }
            return remain >= 3.52 ? "1x1" : null;
        }

        static float FenceMetres(string v) =>
            v == "1x4" ? 12.40f : v == "1x3" ? 9.44f : v == "1x2" ? 6.47f : 3.52f;

        static string FenceStem(string v) =>
            v == "1x1" ? "fence" : "fence_" + v;

        /// HOW DEEP THIS BLOCK'S YARD ACTUALLY IS, AND WHERE ITS CENTRE LINE
        /// RUNS — probed off the built masses, not derived from `TerraceBlock`.
        ///
        /// Walks in from each of the two long faces along the SHORT axis: the
        /// first 2.6m is setback and clear, then the terrace row is solid,
        /// then the yard is clear again. The back of the row is where it goes
        /// clear the second time. False when either face has no terrace at
        /// all — a block with nothing built on it has no yard, and a fence
        /// standing in open ground is the fault this returns false to avoid.
        static bool YardOf(StreetMap.Block block, bool alongX, out float depth, out float mid)
        {
            depth = 0f; mid = 0f;
            double c = alongX ? block.CentreX : block.CentreZ;
            double lo = alongX ? block.MinZ : block.MinX;
            double hi = alongX ? block.MaxZ : block.MaxX;

            float backLo, backHi;
            if (!BackOfRow(alongX, c, lo, +1f, out backLo)) return false;
            if (!BackOfRow(alongX, c, hi, -1f, out backHi)) return false;
            depth = backHi - backLo;
            mid = (backHi + backLo) * 0.5f;
            // Under a metre and a half there is no yard, only a party-wall
            // gap; a boundary there would be geometry inside geometry.
            return depth >= 1.5f;
        }

        /// From a block face, inward, to the far side of the terrace row.
        static bool BackOfRow(bool alongX, double centre, double face, float sign, out float back)
        {
            back = 0f;
            bool entered = false;
            for (float d = 0f; d <= 18f; d += 0.4f)
            {
                float v = (float)face + sign * d;
                var p = alongX ? new Vector3((float)centre, 0, v)
                               : new Vector3(v, 0, (float)centre);
                bool solid = !WorldBuilder.PointClear(p, 0f);
                if (solid) { entered = true; continue; }
                if (entered) { back = v; return true; }
            }
            return false;
        }

        // ---- 3. roadworks ---------------------------------------------------

        /// A CLOSED LANE, WHICH IS THE CHEAPEST DENSITY WIN ON THE BOARD. The
        /// cone is 0.56 x 0.69 x 0.56m against a real 0.5-0.75m, so it needs
        /// no rescale beyond the unit normalisation, and it is 48 vertices.
        /// The barrier is the 1.66m British red-and-white pedestrian barrier.
        ///
        /// AND THE WORKS LAMP IS THE ONLY NEW LIGHT SOURCE IN EITHER KIT. An
        /// amber point at eye height beside a barrier is exactly what the
        /// night frame is short of, and it is the whole reason this model was
        /// chosen over the other two.
        static void Roadworks(Transform parent)
        {
            foreach (var e in StreetMap.Edges)
            {
                if (!e.Driveable || e.Length < 30) continue;
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 1e-3) continue;
                dx /= len; dz /= len;

                double mx = (a.X + b.X) * 0.5, mz = (a.Z + b.Z) * 0.5;
                var district = StreetMap.DistrictAt(a.X, a.Z);
                double share = (district == "Copper Row" || district == "Ironside")
                               ? WorksShareBusy : WorksShareElse;
                if (Dressing.Roll(mx, mz, 74) > share) continue;

                var along = new Vector3((float)dx, 0, (float)dz);
                var across = new Vector3((float)-dz, 0, (float)dx);
                var mid = new Vector3((float)mx, 0, (float)mz);
                int side = Dressing.Roll(mx, mz, 75) < 0.5 ? -1 : 1;
                float half = (float)e.Width * 0.5f;

                // THE CLUSTER IS ITS OWN SITE. Without it a cluster that
                // placed nothing is invisible: every prop count would simply
                // be lower and nothing would say how many clusters there were.
                WorldBuilder.KitTally.Offered("works_cluster");
                int stood = 0;

                // The taper: cones walking from the kerb in to the lane
                // centre, which is what a coning-out actually looks like.
                int cones = 3 + (int)(Dressing.Roll(mx, mz, 76) * 6.0);
                for (int i = 0; i < cones; i++)
                {
                    float s = -cones * 0.8f + i * 1.6f;
                    float off = Mathf.Lerp(half - 0.45f, half * 0.5f, cones < 2 ? 0f : i / (float)(cones - 1));
                    var at = mid + along * s + across * (off * side);
                    WorldBuilder.KitTally.Offered("works_cone");
                    if (!StreetMap.OnRoad(at.x, at.z))
                    { WorldBuilder.KitTally.Refused("works_cone", "off_road"); continue; }
                    if (Stand("works_cone", "", "city_kit_roads_construction_cone", at,
                              Quaternion.identity, 0.69f, ConeOrange, parent) != null) stood++;
                }

                // The barriers close the head of the taper, laid across the
                // shut lane. The model's long axis is its local z, so
                // LookRotation on `across` lies it over the carriageway.
                int bars = 2 + (int)(Dressing.Roll(mx, mz, 77) * 3.0);
                float headS = cones * 0.8f + 1.4f;
                for (int i = 0; i < bars; i++)
                {
                    var at = mid + along * headS
                             + across * ((half - 0.6f - i * 1.66f) * side);
                    WorldBuilder.KitTally.Offered("works_barrier");
                    if (!StreetMap.OnRoad(at.x, at.z))
                    { WorldBuilder.KitTally.Refused("works_barrier", "off_road"); continue; }
                    // ALTERNATING RED AND WHITE. One mesh takes one tint, so a
                    // single barrier cannot be striped — but a RUN of them
                    // alternating reads as the red-and-white barrier line from
                    // across a street, which is the distance this is seen at.
                    var paint = (i % 2 == 0) ? BarrierRed : BarrierWhite;
                    if (Stand("works_barrier", "", "city_kit_roads_construction_barrier", at,
                              Quaternion.LookRotation(across), 0.96f, paint, parent) != null) stood++;
                }

                // One lamp on the outer end of the barrier line, a second at
                // the tail of the taper when the site is a long one.
                int lamps = cones >= 6 ? 2 : 1;
                for (int i = 0; i < lamps; i++)
                {
                    var at = i == 0
                        ? mid + along * headS + across * ((half - 0.6f) * side)
                        : mid + along * (-cones * 0.8f - 1.0f) + across * ((half - 0.55f) * side);
                    WorldBuilder.KitTally.Offered("works_lamp");
                    var go = Stand("works_lamp", "", "city_kit_roads_construction_light", at,
                                   Quaternion.LookRotation(-across), 1.73f, LampAmber, parent);
                    if (go == null) continue;
                    stood++;
                    // WIRED, NOT LIT. `Emit` builds the light dark and hands it
                    // to the night sweep, so this flag says the lamp CARRIES a
                    // registered light — not that it is emitting. It was called
                    // `lit`, and `worksLampsLit=18/18` would have been read as
                    // the night-lighting question answered (audit C3).
                    if (Emit(go, at))
                        WorldBuilder.KitTally.Flagged("works_lamp", KitDressing.FlagNightLight);
                }

                if (stood > 0) WorldBuilder.KitTally.Placed("works_cluster", ""); else WorldBuilder.KitTally.Missed("works_cluster", "");
            }
        }

        /// THE AMBER POINT SOURCE, and the two numbers in it are the project's
        /// own rather than new ones.
        ///
        /// INTENSITY 0.95 is `MakeLamp`'s, which is the one lamp value in this
        /// codebase that came from a measured night floor (its comment calls
        /// it "the linear trim, same reason and ratio as the neon's"). RANGE 6
        /// is half the street lamp's 12, on the physical argument that a 1.73m
        /// works lamp lights its own site and a 5.2m column lights the
        /// carriageway. Neither is a threshold and neither gates anything, and
        /// the NIGHT STILL is what will set them properly.
        ///
        /// `worksLampsWired` IS NOT THAT INSTRUMENT AND THIS PARAGRAPH USED TO
        /// SAY IT WAS, naming the key by its old spelling. It counts lamps that
        /// carry a registered light; it cannot see an intensity, a range, or
        /// whether the sweep ever turned one on. Nothing in this repository
        /// currently measures how much light reaches the night frame from these
        /// lamps, and a comment claiming otherwise is how a settled question
        /// stays unasked.
        ///
        /// IT SWITCHES OFF BY DAY, and the paragraph here used to say it did
        /// not. The gap was real: `WorldBuilder.Lamps` is private and
        /// `SetLampsEnabled` walks only that list, so a Light built outside
        /// that file kept whatever `enabled` it was born with, and
        /// `RegisterNightLight` could not serve because it takes a Renderer
        /// for lit WINDOWS. The trade written here — "left burning is
        /// defensible, a live works site does burn its lamps" — was the wrong
        /// call whatever its merits: every works lamp would have stood lit in
        /// the NOON frame, which is the frame the project is judged on.
        /// `WorldBuilder.RegisterStreetLight` is the registry that did not
        /// exist; the light is born dark and the sweep owns it from there.
        ///
        /// WHAT `false` MEANS, AND IT USED TO MEAN NOTHING. The only false
        /// return was `rends.Length == 0`, and `Stand` already returns null in
        /// that case and destroys colliders only — so a non-null lamp
        /// guaranteed a renderer, `Emit` could not fail, and
        /// `worksLampsLit=18/18` was the same variable printed twice
        /// (audit C3). A numerator computed once per denominator is not a
        /// fraction.
        ///
        /// SO THE PREDICATE IS NOW THE ONE THING THAT CAN ACTUALLY GO WRONG
        /// HERE: the lens is seated at 0.88 of the model's MEASURED height, and
        /// `Stand` skips its normalisation for a mesh under 0.01m tall exactly
        /// as `MakeLamp` skips its own under 0.5m. A lamp that arrives with no
        /// measurable height would take its light to the road surface — a lit
        /// puddle under a barrier and no lamp glow — so it gets no light and is
        /// counted as not wired, which is the reading that would send somebody
        /// to the import scale. Dark and counted beats lit in the ground and
        /// uncounted.
        static bool Emit(GameObject lamp, Vector3 at)
        {
            Bounds bb;
            if (!WorldBounds(lamp, out bb)) return false;
            if (bb.size.y <= 0.01f) return false;
            // The lens sits at 0.88 of the model's height — measured off the
            // FBX, where the lamp head's octagonal lens spans y 17.9 to 23.4
            // of a 23.4-unit model and centres at 20.6.
            var go = new GameObject("WorksLampLight");
            go.transform.SetParent(lamp.transform, false);
            go.transform.position = new Vector3(bb.center.x, at.y + bb.size.y * 0.88f, bb.center.z);
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 6f;
            light.intensity = 0.95f;
            light.color = new Color(1f, 0.66f, 0.25f);
            // Born dark and handed to the night sweep, which owns the state.
            // Setting it true here is what put an amber pool under every
            // barrier at noon; the sweep's guard keys on the lamp COUNT, so
            // registering after the last state change is already handled.
            light.enabled = false;
            WorldBuilder.RegisterStreetLight(light);
            return true;
        }

        /// SATURATED AT SOURCE, because the noir grade desaturates everything
        /// downstream — the no-entry disc in `StreetFurniture` records
        /// exactly this: on `BrickRed` the grade left "a grey lollipop", and
        /// a sign that is not red is not a sign.
        static readonly Color ConeOrange = new Color(0.86f, 0.33f, 0.06f);
        static readonly Color BarrierRed = new Color(0.62f, 0.10f, 0.10f);
        static readonly Color BarrierWhite = new Color(0.78f, 0.77f, 0.73f);
        static readonly Color LampAmber = new Color(0.85f, 0.55f, 0.10f);

        // ---- the one placement primitive ------------------------------------

        /// THE WORLD BOUNDS OF A STANDING PROP, or false when it has nothing
        /// to draw. One implementation: `Emit` walked the renderers itself and
        /// the planter site needed the same walk, and two copies of a bounds
        /// encapsulation is the shape where one of them forgets to start from
        /// `rends[0]` and encloses the origin. `Stand` keeps its own walks
        /// deliberately — it re-reads the SAME cached renderer array after each
        /// transform, which is a different operation from asking a finished
        /// object how big it is.
        static bool WorldBounds(GameObject go, out Bounds b)
        {
            b = new Bounds();
            var rends = go.GetComponentsInChildren<Renderer>();
            if (rends.Length == 0) return false;
            b = rends[0].bounds;
            foreach (var r in rends) b.Encapsulate(r.bounds);
            return true;
        }

        /// INSTANTIATE, NORMALISE, SEAT, TINT, STRIP — `MakeLamp`'s shape,
        /// which re-measures the bounds after every transform for the reason
        /// its own comment gives: the scale of an imported model is not a
        /// thing to assume.
        ///
        /// FILES THE OUTCOME ITSELF so that no call site can place a prop and
        /// forget to say whether it landed. The caller files `Offered`; this
        /// files exactly one of `Placed`/`Missed`, including the case where
        /// the prefab loads but carries no renderer — an object with nothing
        /// to draw is a miss whatever the loader returned.
        /// INTERNAL, NOT PRIVATE, since the street nameplates. `StreetFurniture`
        /// stands the `road-sign-object-street` blade and needed exactly this —
        /// instantiate, normalise off measured bounds, seat, tint through the
        /// shared repaint, strip colliders, file the outcome. Copying the shape
        /// into that file would have been the second implementation of the one
        /// idea, in the same batch whose whole first task was deleting a second
        /// implementation of the lettering idiom.
        internal static GameObject Stand(string family, string variant, string key, Vector3 at,
                                Quaternion rot, float metresTall, Color paint, Transform parent)
        {
            var go = AssetLibrary.TryInstantiateProp(key, at, rot);
            if (go == null) { WorldBuilder.KitTally.Missed(family, variant); return null; }

            var rends = go.GetComponentsInChildren<Renderer>();
            if (rends.Length == 0)
            {
                Object.Destroy(go);
                WorldBuilder.KitTally.Missed(family, variant);
                return null;
            }

            var b = rends[0].bounds;
            foreach (var r in rends) b.Encapsulate(r.bounds);
            if (b.size.y > 0.01f) go.transform.localScale *= metresTall / b.size.y;

            // Re-read: the scale moved every one of them.
            b = rends[0].bounds;
            foreach (var r in rends) b.Encapsulate(r.bounds);
            go.transform.position += Vector3.up * (at.y - b.min.y);

            go.transform.SetParent(parent, true);
            go.name = "SD_" + key;
            // Through the shared repaint, so the family lands in `kitAlbedo`
            // with a painter's name against it — a private tint here is how
            // `Furniture` once shipped a factory-white swing bin through a
            // build in which WorldBuilder's bins went metal.
            WorldBuilder.TintFurniture(go, paint, key);
            // No colliders on dressing. A player who can be stopped by a cone
            // is a player fighting the scenery, and every other placer in this
            // family strips for the same reason.
            foreach (var c in go.GetComponentsInChildren<Collider>()) Object.Destroy(c);

            WorldBuilder.KitTally.Placed(family, variant);
            return go;
        }
    }
}
