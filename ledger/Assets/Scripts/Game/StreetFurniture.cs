using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Signs (roadmap M12, step 4).
    ///
    /// Traffic control the player can READ. The rules already exist in Core —
    /// lights at the four big crossings, stop signs everywhere else, lanes that
    /// are not through roads — but a rule the city obeys without telling you is
    /// indistinguishable from arbitrary behaviour. A car stopping at an empty
    /// junction looks like a bug until there is a sign there.
    ///
    /// Street names do more work than the signs do. An address is the unit
    /// people give directions in and gossip in, and the plates read from the
    /// same table as the witness lines, so the city cannot tell the player one
    /// name and a character another.
    public static class StreetFurniture
    {
        public static int SignCount { get; private set; }

        public static void Build()
        {
            SignCount = 0;
            WallPlateCount = 0;
            // Cumulative over ONE Build, so they reset with it: the cables
            // and the pole wires both string through `Segment` and both
            // count here.
            WireSegments = 0;
            WireSegmentsDark = 0;
            foreach (var n in StreetMap.Nodes)
            {
                if (!n.IsJunction) continue;
                BuildNamePlates(n);
                if (!Signals.HasLights(n)) BuildStopSigns(n);
            }
            BuildLaneSigns();
            BuildOverheadCables();
            BuildTelegraphPoles();
            // The surface-history layer builds in the same phase as the
            // cables and reads the same street map, prosperity constants and
            // deterministic rolls — one dressing pass, several vocabularies.
            DecalLayer.Build();
            // And the objects themselves: bins, bollards, benches, dock
            // clutter, double yellows — same phase, same rolls.
            Furniture.Build();
        }

        /// How many cables got strung. Read by the sim, for the same reason
        /// `Dressed` is: "the street feels enclosed" has to be a count.
        public static int CableCount { get; private set; }

        /// CABLES ACROSS THE STREET — `Dressing.CableAt`, which has been on the
        /// reach ledger since the ledger was written.
        ///
        /// Its own comment says it: *"Overhead clutter is the cheapest thing
        /// there is for making a street feel ENCLOSED rather than like two rows
        /// of boxes with a gap, and nobody ever budgets for it."* The function
        /// was written, tested, entered on the debt ledger as "authored in
        /// Dressing and drawn nowhere", and left. `built is not running`, in the
        /// one system whose entire job is to stop the city reading as two rows
        /// of boxes with a gap — which is precisely how the review still reads.
        ///
        /// The span is the edge's own width, so `CableAt`'s 14m cutoff does the
        /// deciding: alleys and streets get cables, and a wide avenue does not,
        /// because a cable over a main road reads as a mistake rather than as a
        /// slum. Prosperity is the back-alley figure on a lane and the
        /// street-front figure otherwise — the same two constants the facades
        /// are dressed from, so a poor lane strings more than a good street.
        static void BuildOverheadCables()
        {
            CableCount = 0;
            foreach (var e in StreetMap.Edges)
            {
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 1e-3) continue;
                dx /= len; dz /= len;
                double prosperity = e.Kind == "lane" ? 0.15 : 0.55;

                // Every seven metres along, which is far enough apart that two
                // cables never read as a net and close enough that a short lane
                // still gets one.
                for (double s = 6.0; s < len - 6.0; s += 7.0)
                {
                    double x = a.X + dx * s, z = a.Z + dz * s;
                    if (!Dressing.CableAt(x, z, prosperity, e.Width)) continue;
                    if (Cable(x, z, dx, dz, e.Width)) CableCount++;
                }
            }
        }

        public static int PoleCount { get; private set; }
        public static int PoleWireCount { get; private set; }

        /// TELEGRAPH POLES ALONG THE AVENUES (M17.10 V3's named gap). The
        /// cross-street cables partition the town with `CableAt`: lanes and
        /// streets string building-to-building, and a wide avenue stays bare
        /// because a cable across a main road reads as a mistake. But the
        /// reference frames carry pole-borne wires ALONG their wide streets
        /// — the avenues are where the camera lives, and they were the one
        /// place with empty sky by design rather than by look. A wooden
        /// pole every thirty metres down one side, two wires sagging
        /// span to span. One side per avenue, chosen from the edge's own
        /// endpoints so it cannot flip between builds; a pole that cannot
        /// stand clear of the furniture drops its span rather than standing
        /// in a doorway (the wire line resumes at the next pole).
        static void BuildTelegraphPoles()
        {
            PoleCount = 0; PoleWireCount = 0;
            foreach (var e in StreetMap.Edges)
            {
                if (e.Kind != "avenue") continue;
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                double dx = b.X - a.X, dz = b.Z - a.Z;
                double len = System.Math.Sqrt(dx * dx + dz * dz);
                if (len < 45) continue;   // a short stub gets no line
                dx /= len; dz /= len;
                var across = new Vector3((float)-dz, 0, (float)dx);
                int side = ((Mathf.RoundToInt((float)(a.X + b.Z)) & 1) == 0) ? 1 : -1;
                // Past the kerb onto the pavement — the road half plus a
                // pole's own stand-off, inside the building setback.
                float off = (float)e.Width * 0.5f + 0.9f;
                Vector3? prevTop = null;
                for (double s = 14.0; s < len - 14.0; s += 30.0)
                {
                    var basePos = new Vector3((float)(a.X + dx * s), 0,
                                              (float)(a.Z + dz * s))
                                  + across * (side * off);
                    if (!WorldBuilder.PointClear(basePos, 0f)) { prevTop = null; continue; }
                    Pole(basePos, across);
                    PoleCount++;
                    var top = basePos + Vector3.up * 6.6f;
                    if (prevTop.HasValue)
                    {
                        Wires(prevTop.Value, top, across);
                        PoleWireCount += 2;
                    }
                    prevTop = top;
                }
            }
        }

        /// A pole is a post and a crossarm; the arm runs perpendicular to
        /// the wires, which is what spreads the pair apart. Wood, because
        /// a late-analog British pole is creosoted timber, and the tint
        /// system already owns the colour.
        static void Pole(Vector3 basePos, Vector3 across)
        {
            var post = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            post.name = $"Pole_{basePos.x:0}_{basePos.z:0}";
            post.transform.position = basePos + Vector3.up * 3.5f;
            post.transform.localScale = new Vector3(0.18f, 3.5f, 0.18f);
            post.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Wood);
            Strip(post.GetComponent<Collider>());
            var arm = GameObject.CreatePrimitive(PrimitiveType.Cube);
            arm.name = post.name + "_arm";
            arm.transform.position = basePos + Vector3.up * 6.5f;
            arm.transform.rotation = Quaternion.FromToRotation(Vector3.right, across.normalized);
            arm.transform.localScale = new Vector3(1.4f, 0.09f, 0.09f);
            arm.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Wood);
            Strip(arm.GetComponent<Collider>());
        }

        /// Two wires between crossarm ends, each sagging through a low
        /// middle — the same two-segment weight trick the cross-street
        /// cables use, for the same reason.
        static void Wires(Vector3 fromTop, Vector3 toTop, Vector3 across)
        {
            var d = across.normalized;
            foreach (float w in new[] { -0.5f, 0.5f })
            {
                var f = fromTop + d * w;
                var t = toTop + d * w;
                var low = (f + t) * 0.5f - Vector3.up * 0.5f;
                Segment($"PoleWire_{f.x:0}_{f.z:0}_{w:0.0}a", f, low);
                Segment($"PoleWire_{f.x:0}_{f.z:0}_{w:0.0}b", low, t);
            }
        }

        /// One cable, as two sagging segments.
        ///
        /// TWO AND NOT ONE, because a dead-straight line at six metres reads as
        /// scaffolding. Two segments meeting a third of a metre lower in the
        /// middle is the cheapest thing that reads as weight — a real catenary
        /// would be a mesh, and at this distance in fog nobody can tell the
        /// difference between a curve and one bend.
        static bool Cable(double x, double z, double dx, double dz, double span)
        {
            // Across the street, not along it: the perpendicular.
            var across = new Vector3((float)-dz, 0, (float)dx);
            var mid = new Vector3((float)x, 0, (float)z);
            // TO THE BUILDING LINE, not the kerb. The building faces sit
            // BlockSetback behind the block edge, and a half-span of
            // road-width + 0.6 left every cable ending in MID-AIR above the
            // pavement — both landed town-plan builds show the result: bent
            // black scribbles floating against the sky, anchored to nothing.
            // Road half + setback + 0.6 buries the ends in the terrace faces.
            float half = (float)span * 0.5f + WorldBuilder.BlockSetback + 0.6f;
            // AND ONLY WHERE BOTH ENDS HAVE A BUILDING TO HOLD THEM. The
            // extension fixed the geometry; it cannot conjure a wall where a
            // parcel was skipped, and the third landed build still showed one
            // scribble over a gap. A cable is a thing two buildings agree on.
            var endA = mid - across * ((float)span * 0.5f + WorldBuilder.BlockSetback * 0.5f);
            var endB = mid + across * ((float)span * 0.5f + WorldBuilder.BlockSetback * 0.5f);
            if (!WorldBuilder.MassAt(endA, 2.0f, out _, out _)) return false;
            if (!WorldBuilder.MassAt(endB, 2.0f, out _, out _)) return false;
            const float high = 6.0f, sag = 0.35f;
            var left = mid - across * half + Vector3.up * high;
            var right = mid + across * half + Vector3.up * high;
            var low = mid + Vector3.up * (high - sag);
            Segment($"Cable_{x:0}_{z:0}_a", left, low);
            Segment($"Cable_{x:0}_{z:0}_b", low, right);
            return true;
        }

        /// How many span segments got built, and how many of them took the
        /// near-black wire material. Both are CUMULATIVE over one Build();
        /// the second is the numerator and the first is its denominator, so
        /// "no spans were darkened" and "no spans exist" cannot read alike.
        /// NOT `CableCount` IN OTHER UNITS, and the identity says so: a
        /// cable is two segments and a pole wire is two segments, so a
        /// healthy run has `WireSegments == 2*(cables + poleWires)` — 318
        /// against the landed `cables=63 poleWires=96`. A reading that
        /// breaks that identity is a span built through some other path,
        /// which is the thing this pair exists to make visible.
        public static int WireSegments { get; private set; }
        public static int WireSegmentsDark { get; private set; }

        /// WHICH PROPERTIES THE SHADER ACTUALLY ACCEPTED, as a `+`-joined
        /// token — the one thing about this change that can fail silently.
        /// Setting a property a shader does not have is a no-op that neither
        /// errors nor changes anything, and this project has shipped that
        /// twice (see `PaintKit`, which counts acceptances rather than calls
        /// for the same reason). Last-wins over the single derived material,
        /// which is correct because there is exactly one. The default is the
        /// words `nothing_measured`, so a build where the material was never
        /// derived cannot read as a build where the shader refused
        /// everything.
        public static string WireProps { get; private set; } = "nothing_measured";

        /// THE WIRE'S OWN MATERIAL — near-black and matte, because the shared
        /// `Metal` surface is neither.
        ///
        /// MEASURED BEFORE CHANGED, off `review_day5_noon` — a frame whose
        /// row in `frames.tsv` reads `rain=0.00 wet=0.00`, so nothing in it
        /// is a rain streak. The span crossing the sky there reads a MEDIAN
        /// 2.77x the luma of the sky in the SAME COLUMN (11 columns sampled,
        /// each denominator taken from the same frame 14px off the wire),
        /// peaking at RGB 231,243,243: a blown-out white scratch with a
        /// specular blob where the sun catches it. A silhouette element that
        /// reads BRIGHTER than the sky behind it is the one failure mode
        /// overhead clutter has.
        ///
        /// The cause is the shared surface, not the geometry: `metal` is
        /// tint 0.30/0.31/0.33 at metallic 0.9 and smoothness 0.55, which is
        /// a mirror. A thin cylinder sweeps every normal across its width, so
        /// somewhere along it the specular condition is always met and the
        /// whole span lights up at once.
        ///
        /// DERIVED, NOT EDITED IN PLACE: 45 other call sites take
        /// `AssetLibrary.Metal` — bench legs, dumpsters, bar counters, roof
        /// aerials — and a mirror is right for most of them. One material is
        /// derived once and shared by every span, so batching survives; the
        /// pattern is `MaterialGraded`'s.
        ///
        /// A MATERIAL RATHER THAN `PaintKit`, and the difference is the
        /// point. `PaintKit` is right for a KIT MESH whose own material is
        /// already matte, where only the colour is wrong. Here half the fault
        /// is the GLOSS, which no colour set can reach, and a property block
        /// would also skip the gamma-to-linear conversion that
        /// `Material.SetColor` performs — a display-authored near-black would
        /// come out weaker than authored. One shared material has neither
        /// problem.
        ///
        /// The values are the palette's, not invented here. The colour is
        /// `TrafficHost.SignalHousing`'s (0.13/0.15/0.14), near-black and
        /// faintly green, whose own comment asks for "the same family as the
        /// lamp column so the street's ironwork agrees with itself" — a span
        /// is street ironwork. The smoothness and metallic are `Roof`'s
        /// (0.12 / 0.1), the palette's existing entry for weathered outdoor
        /// metal, which leaves the thin highlight a real wire keeps at night
        /// without the daylight mirror.
        static readonly Color WireBlack = new Color(0.13f, 0.15f, 0.14f);
        const float WireSmoothness = 0.12f;
        const float WireMetallic = 0.10f;
        static Material _wireMat;

        static Material WireMaterial()
        {
            // Unity's null check also catches a material destroyed with the
            // previous scene, so a rebuild derives a fresh one.
            if (_wireMat != null) return _wireMat;
            var baseMat = AssetLibrary.Material(AssetLibrary.Metal);
            if (baseMat == null) { WireProps = "no_base_material"; return null; }
            var mat = new Material(baseMat) { name = "wire_black" };
            var took = "";
            if (mat.HasProperty("_Color")) { mat.SetColor("_Color", WireBlack); took += "+color"; }
            if (mat.HasProperty("_Metallic")) { mat.SetFloat("_Metallic", WireMetallic); took += "+metallic"; }
            // A BOUND GLOSS MAP MAKES `_Glossiness` A NO-OP, which is the
            // same silent failure one layer down: with `_METALLICGLOSSMAP`
            // enabled the Standard shader reads smoothness from the map's
            // alpha and ignores the scalar. `SetWetness` hit this and drives
            // `_GlossMapScale` instead when a map is bound; same answer here.
            // Whether `metal` carries one depends on what the texture pack
            // shipped, so BOTH are set and the token says which took.
            if (mat.HasProperty("_Glossiness")) { mat.SetFloat("_Glossiness", WireSmoothness); took += "+gloss"; }
            if (mat.IsKeywordEnabled("_METALLICGLOSSMAP") && mat.HasProperty("_GlossMapScale"))
            { mat.SetFloat("_GlossMapScale", WireSmoothness); took += "+glossmap"; }
            WireProps = took.Length == 0 ? "none_accepted" : took.Substring(1);
            _wireMat = mat;
            return mat;
        }

        static void Segment(string name, Vector3 from, Vector3 to)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = (from + to) * 0.5f;
            go.transform.up = (to - from).normalized;
            go.transform.localScale = new Vector3(0.05f, (to - from).magnitude, 0.05f);
            WireSegments++;
            var wire = WireMaterial();
            go.GetComponent<Renderer>().sharedMaterial =
                wire != null ? wire : AssetLibrary.Material(AssetLibrary.Metal);
            if (wire != null) WireSegmentsDark++;
            Strip(go.GetComponent<Collider>());
        }

        /// How many plates are mounted on walls. Separate from SignCount on
        /// purpose: SignCount answers "how much sign FURNITURE stands in the
        /// street", and a plate screwed to a building stands in nobody's way.
        public static int WallPlateCount { get; private set; }

        /// Street names at each junction. TOWN-PLAN.MD T2 under the flag:
        /// plates are MOUNTED ON THE CORNER BUILDING, as a British council
        /// mounts them — the NS street's name on the wall you see walking
        /// that street, the EW name round the corner. The terrace generator
        /// guarantees corners are buildings (Z-rows own them), so quadrants
        /// are tried until one has a wall whose two junction-facing faces are
        /// both exposed; only a junction with no wall at all (the map's cut
        /// corners, Ironside's yards) falls back to one clustered post —
        /// which is also what a council does. Legacy path: post always.
        ///
        /// BOTH MOUNTS NOW HANG THE KIT BLADE (`NamePlate`), not a primitive
        /// board: `road-sign-object-street` is a 3.2:1 plate and is the
        /// British form, where the kit's `road-sign-street` pole is the
        /// American one and the survey rejected it. The board survives as the
        /// fallback when the model is not in the build, because a nameplate's
        /// content is the NAME and a lettered board still delivers it.
        static void BuildNamePlates(StreetNode n)
        {
            if (!StreetMap.NamesAt(n, out var ns, out var ew))
            {
                // A JUNCTION THAT CANNOT SAY WHAT IT IS — OFFERED AND REFUSED,
                // NOT SKIPPED, and the difference is the whole readability of
                // this key. `StreetMap.NamesAt` returns names for exactly ONE
                // of this city's 97 junctions (measured 25 Aug by compiling
                // Core alone and counting; see the report), so a silent skip
                // would print `sign_plate_name:2/2/0/0refused` — which reads
                // as a placer that hardly ran, when the truth is a placer that
                // ran at every junction in the city and was given a name at
                // one of them. Two sites per junction, because a junction
                // offers a plate per street.
                //
                // THE CAUSE IS IN CORE AND IS NOT FIXED HERE: `NameOf`
                // compares SCALED node coordinates against the UNSCALED
                // district avenue tables, so only the founding cross at
                // (0,0) — which `WideBlocks` scaling leaves fixed — can match.
                // That is the sixth consumer of those tables to read them raw
                // and the fix belongs with the five already recorded in
                // `BoundsOf`'s comment, not in a signage commit. Until then
                // `kitRefusedBy` carries `junction_unnamed` with its count,
                // every run, which is the number that says so.
                for (int i = 0; i < 2; i++)
                {
                    WorldBuilder.KitTally.Offered("sign_plate_name");
                    WorldBuilder.KitTally.Refused("sign_plate_name", "junction_unnamed");
                }
                return;
            }

            if (WorldBuilder.TownPlanEnabled)
            {
                float half = (float)StreetMap.AvenueWidth / 2f;
                float toCorner = half + WorldBuilder.BlockSetback + 2.5f;
                foreach (var (qx, qz) in new[] { (1f, 1f), (-1f, 1f), (1f, -1f), (-1f, -1f) })
                {
                    var probe = new Vector3((float)n.X + qx * toCorner, 0,
                                            (float)n.Z + qz * toCorner);
                    if (!WorldBuilder.MassAt(probe, 3f, out var mp, out var ms)) continue;

                    // The two faces looking back at the junction's streets —
                    // and both must be real frontages, not party walls: a
                    // probe that landed on a mid-row parcel (yard-gate gap,
                    // alley) offers a face with a neighbour pressed against
                    // it, and a plate there would be buried in brick.
                    float fx = mp.x - qx * ms.x / 2f;
                    float fz = mp.z - qz * ms.z / 2f;
                    float pz = fz + qz * 1.6f;   // 1.6m round the corner, each way
                    float px = fx + qx * 1.6f;
                    if (!WorldBuilder.PointClear(new Vector3(fx - qx * 0.3f, 0, pz), 0f)) continue;
                    if (!WorldBuilder.PointClear(new Vector3(px, 0, fz - qz * 0.3f), 0f)) continue;

                    // ALONG THE WALL, AND OUT OF IT. The NS plate hangs on the
                    // x-facing wall at `fx`, so it runs along z and looks back
                    // along -qx; the EW plate is the same statement with the
                    // axes swapped. `NamePlate` needs both because a BLADE has
                    // to lie the long way along its wall, where a flat board
                    // did not care.
                    NamePlate($"NamePlate_{n.Id}_ns", new Vector3(fx - qx * 0.05f, 2.7f, pz), ns, 90f,
                              new Vector3(0, 0, 1), new Vector3(-qx, 0, 0));
                    NamePlate($"NamePlate_{n.Id}_ew", new Vector3(px, 2.7f, fz - qz * 0.05f), ew, 0f,
                              new Vector3(1, 0, 0), new Vector3(0, 0, -qz));
                    WallPlateCount += 2;
                    return;
                }
            }

            float d = (float)StreetMap.AvenueWidth / 2f + 2.0f;
            var basePos = new Vector3((float)n.X - d, 0, (float)n.Z + d);

            // ON A LOW POST, and the two blades cross at right angles the way
            // a council's clustered post does — each one reading along the
            // street it names. Same `NamePlate`, so a junction with no corner
            // wall gets the same object as one with a wall, at a different
            // mount.
            Post($"NamePost_{n.Id}", basePos, 3.0f);
            NamePlate($"NamePlate_{n.Id}_ns", basePos + new Vector3(0, 2.75f, 0), ns, 90f,
                      new Vector3(0, 0, 1), new Vector3(-1, 0, 0));
            NamePlate($"NamePlate_{n.Id}_ew", basePos + new Vector3(0, 2.40f, 0), ew, 0f,
                      new Vector3(1, 0, 0), new Vector3(0, 0, -1));
            SignCount += 2;
        }

        /// A stop sign on every approach that actually exists. The outer ring has
        /// three approaches, not four, and a sign facing empty ground is the kind
        /// of detail that quietly tells the player the world is generated.
        ///
        /// TOWN-PLAN.MD T1, and the largest single sign class dies here: under
        /// the flag a minor junction is marked the way a British one is — a
        /// double broken bar PAINTED across the entering lane — because give-way
        /// posts on every approach of every junction is American grammar and,
        /// at this density, is most of what read as sign spam. The rule stays
        /// readable (a car halting at the line has a line to halt at); paint is
        /// not a sign, so SignCount stops counting these, which is the point.
        static void BuildStopSigns(StreetNode n)
        {
            foreach (var e in StreetMap.EdgesAt(n.Id))
            {
                if (!e.Driveable) continue;
                var other = StreetMap.Node(StreetMap.Other(e, n.Id));
                if (other == null) continue;

                // Set back down the approaching road, on the driver's right.
                float dx = (float)(other.X - n.X), dz = (float)(other.Z - n.Z);
                float len = Mathf.Sqrt(dx * dx + dz * dz);
                if (len < 0.001f) continue;
                dx /= len; dz /= len;

                if (WorldBuilder.TownPlanEnabled)
                {
                    // Two broken bars across the inbound lane, just past the
                    // junction pad. Lane centre is a quarter road-width to the
                    // driver's right of the centreline; the bar spans local x,
                    // which under this yaw lies across the carriageway. Same
                    // height and material as the centre-line dashes so all road
                    // paint reads as one system.
                    float backP = (float)StreetMap.AvenueWidth / 2f + 0.8f;
                    float laneW = Mathf.Max(1.5f, (float)e.Width / 2f - 0.5f);
                    foreach (var off in new[] { 0f, 0.45f })
                    {
                        var bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        bar.name = $"GiveWay_{n.Id}_{other.Id}_{off:0.00}";
                        bar.transform.position = new Vector3(
                            (float)n.X + dx * (backP + off) - dz * (float)e.Width / 4f, 0.05f,
                            (float)n.Z + dz * (backP + off) + dx * (float)e.Width / 4f);
                        bar.transform.localScale = new Vector3(laneW, 0.02f, 0.18f);
                        bar.transform.rotation = Quaternion.Euler(0, Mathf.Atan2(dx, dz) * Mathf.Rad2Deg, 0);
                        bar.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Sidewalk);
                        Strip(bar.GetComponent<Collider>());
                    }
                    continue;
                }

                float back = (float)StreetMap.AvenueWidth / 2f + 1.4f;
                float side = (float)e.Width / 2f + 1.2f;
                // Right of an inbound driver (travelling -d) is (-dz, dx).
                var at = new Vector3((float)n.X + dx * back - dz * side, 0,
                                     (float)n.Z + dz * back + dx * side);

                Post($"StopPost_{n.Id}_{other.Id}", at, 2.4f);
                var face = GameObject.CreatePrimitive(PrimitiveType.Cube);
                face.name = $"StopSign_{n.Id}_{other.Id}";
                face.transform.position = at + new Vector3(0, 2.2f, 0);
                face.transform.localScale = new Vector3(0.78f, 0.78f, 0.07f);
                // Turned on its point: at graybox scale a diamond reads as
                // "octagon" far better than a cube reads as anything.
                face.transform.rotation = Quaternion.Euler(0, Mathf.Atan2(dx, dz) * Mathf.Rad2Deg, 45f);
                face.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.BrickRed);
                Strip(face.GetComponent<Collider>());
                SignCount++;
                // No lettering on these. A red diamond on a post at a junction
                // already reads as "stop", and the alternative was a hundred and
                // forty-four TextMesh renderers — which do not batch — to say
                // something the shape says on its own. The street names get text
                // because a name cannot be inferred from a shape.
            }
        }

        /// Lanes are the connectors to doorways, not through roads. Traffic in
        /// Core already refuses to thread them; this is the sign that says so, so
        /// a player who walks up one understands what they are looking at.
        static void BuildLaneSigns()
        {
            foreach (var e in StreetMap.Edges)
            {
                if (e.Driveable) continue;
                var a = StreetMap.Node(e.A);
                var b = StreetMap.Node(e.B);
                if (a == null || b == null) continue;
                // The junction end is the end somebody could drive in from.
                var junction = a.IsJunction ? a : b.IsJunction ? b : null;
                var doorway = junction == a ? b : a;
                if (junction == null) continue;

                float dx = (float)(doorway.X - junction.X), dz = (float)(doorway.Z - junction.Z);
                float len = Mathf.Sqrt(dx * dx + dz * dz);
                if (len < 0.001f) continue;
                dx /= len; dz /= len;
                var at = new Vector3((float)junction.X + dx * 6f - dz * 2.4f, 0,
                                     (float)junction.Z + dz * 6f + dx * 2.4f);

                Post($"LanePost_{e.A}_{e.B}", at, 2.1f);
                var disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                disc.name = $"NoEntry_{e.A}_{e.B}";
                disc.transform.position = at + new Vector3(0, 1.95f, 0);
                disc.transform.localScale = new Vector3(0.62f, 0.05f, 0.62f);
                disc.transform.rotation = Quaternion.Euler(90f, Mathf.Atan2(dx, dz) * Mathf.Rad2Deg, 0);
                disc.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Plaster);
                // Actually red. On BrickRed the noir grade left a grey
                // lollipop — the first landed T1 build shows one mid-frame —
                // and a no-entry sign that is not red is not a sign.
                WorldBuilder.Tint(disc, new Color(0.60f, 0.09f, 0.09f));
                Strip(disc.GetComponent<Collider>());
                SignCount++;
            }
        }

        /// Bus stops and cab ranks drawn, and the count.
        public static int TransitCount { get; private set; }

        /// THE BUS ALREADY STOPS; NOTHING SAYS WHERE.
        ///
        /// `TrafficSim.BusLoop` and `TrafficSim.Ranks` have been on the reach
        /// ledger since it was written, and BOTH REASONS WERE WRONG in the
        /// direction that wastes a day. `BusLoop` said "the bus route exists and
        /// no bus is drawn following it" — a bus IS spawned onto the loop by
        /// `Populate`, `RouteBusFrom` keeps it there, `IsBusStop` makes it dwell
        /// every third junction, and `TrafficHost` draws every vehicle by kind.
        /// The whole behaviour runs. `Ranks` had already been half-corrected on
        /// 4 August — taxis do wait on ranks — and its remaining note names the
        /// real gap in one clause: "nothing draws a rank, signs one".
        ///
        /// That is the same gap for both, and it is the interesting one. A bus
        /// that halts for eight seconds at an unmarked corner is a bug to
        /// anybody watching; the same halt beside a post with a sign on it is a
        /// bus route. `StreetFurniture` exists for exactly this argument and
        /// makes it in its own header — *"a rule the city obeys without telling
        /// you is indistinguishable from arbitrary behaviour. A car stopping at
        /// an empty junction looks like a bug until there is a sign there."*
        /// Written about stop signs, true of this, and nobody applied it.
        ///
        /// FROM THE SIM'S OWN ROUTE, NOT A SECOND COPY OF IT. The loop is
        /// derivable from `StreetMap` alone, so this could have recomputed it
        /// and been right today — and would be the fourth "one idea, two
        /// implementations" in this project, with the marker drifting off the
        /// route the first time either rule changed and nothing to report it.
        /// The sim is passed in and asked.
        public static void BuildTransit(TrafficSim sim)
        {
            TransitCount = 0;
            if (sim == null) return;

            foreach (var id in sim.BusLoop)
            {
                if (!sim.IsBusStop(id)) continue;
                var n = StreetMap.Node(id);
                if (n == null) continue;
                // OFF THE CARRIAGEWAY, on the same reasoning the bins are
                // pulled back to their walls: a post standing in a running lane
                // is a permanent obstruction to a sim that treats geometry as
                // real. Four metres out along the diagonal clears an avenue
                // junction's corner without needing a footway lookup that does
                // not exist.
                var at = new Vector3((float)n.X + 4f, 0, (float)n.Z + 4f);
                Post($"BusStop_{id}_post", at, 2.6f);
                Plate($"BusStop_{id}", at + new Vector3(0, 2.35f, 0), "BUS", 45f);
                TransitCount++;
            }

            foreach (var id in sim.Ranks)
            {
                var n = StreetMap.Node(id);
                if (n == null) continue;
                var at = new Vector3((float)n.X + 4f, 0, (float)n.Z - 4f);
                Post($"Rank_{id}_post", at, 2.6f);
                Plate($"Rank_{id}", at + new Vector3(0, 2.35f, 0), "TAXI", -45f);
                TransitCount++;
            }
        }

        // ---- pieces ----

        static void Post(string name, Vector3 at, float height)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.position = at + new Vector3(0, height / 2f, 0);
            go.transform.localScale = new Vector3(0.1f, height, 0.1f);
            go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);
            Strip(go.GetComponent<Collider>());
        }

        /// A STREET NAMEPLATE — the kit blade if the model is in the build, the
        /// primitive board if it is not, and the NAME lettered onto whichever
        /// one stood.
        ///
        /// WHY IT IS A PLATE AND NOT A POLE. `kit-survey.md` measured
        /// `road-sign-object-street` at 0.31 x 0.44 x 1.42m — a 3.2:1 blade,
        /// which is exactly a British street nameplate (a typical UK plate is
        /// ~1.2m x 0.3m). Its sibling `road-sign-street`, the tall crossblade
        /// on a 3.5m pole, is the AMERICAN form and the survey REJECTED it on
        /// country grounds. Rejecting the pole while placing the plate is the
        /// whole finding, so nothing here may reach for the pole later.
        ///
        /// WHY IT MUST BE LETTERED AND WHY THAT IS THE WHOLE QUESTION. The kit
        /// ships a FLAT PALETTE TEXTURE: the blade carries no glyphs and never
        /// could, so a blade placed as-is is a blank white board in the frame,
        /// which reads as a fault rather than as dressing — and delivers none
        /// of the reason this item was built. The lettering is
        /// `WorldBuilder.Letter`, the shared idiom this batch extracted from
        /// its two private copies precisely so signage would not mint a third.
        ///
        /// ORIENTED BY MEASUREMENT, NEVER BY AN ASSUMED FBX AXIS ORDER. Which
        /// local axis is the blade's long one is a fact this container cannot
        /// read and the build can, so the blade is stood, its world bounds are
        /// encapsulated, and it is given a quarter turn about its mounting
        /// point if the long horizontal extent came out ACROSS the wall
        /// instead of along it. Same reasoning as `Stand` re-reading bounds
        /// after every transform: the scale and the axis order of an imported
        /// model are things to read, not to assume.
        ///
        /// THE BOARD FALLBACK IS NOT A DECOY, and that is a deliberate
        /// departure from `StreetDressing`, which refuses fallback primitives
        /// outright. Its reasoning is right for a planter: a grey box at the
        /// right size hides a miss, and a planter's whole content is its
        /// shape. A nameplate's content is the NAME — a lettered board
        /// delivers all of it and a bare junction delivers none — so the
        /// board stays. `Missed` is filed either way, so the count still says
        /// which mesh actually stood.
        ///
        /// EVERY SITE AND EVERY OUTCOME IS FILED WITH `WorldBuilder.KitTally`,
        /// the project's ONE `KitDressing` instance. `sign_plate_name` has
        /// printed `nothing-offered` every run since the catalogue named it;
        /// this is the call that changes that, and rule 6 is why the counter
        /// ships in the same edit as the placement rather than after it.
        static void NamePlate(string name, Vector3 at, string text, float yaw,
                              Vector3 alongWall, Vector3 outward)
        {
            WorldBuilder.KitTally.Offered("sign_plate_name");

            // SEATED BY ITS MIDDLE, NOT BY ITS FOOT. `Stand` puts a prop's
            // bottom on `at.y`, which is right for a cone and wrong for a
            // plate hung at a height — so the anchor is dropped by half the
            // blade's true height and the blade's middle lands where the
            // board's middle was. 0.44m is the FBX's own 6.00 units x 0.074,
            // from `tools/prop-dimensions.py`, not from a convention.
            var go = StreetDressing.Stand(
                "sign_plate_name", "", "road-sign-object-street",
                at - new Vector3(0, BladeTall / 2f, 0),
                Quaternion.Euler(0, yaw, 0), BladeTall, PlateEnamel, null);

            // The blade's measured length along its wall, and how far the
            // glyphs must sit out of its face. Both start at the primitive
            // board's numbers and are replaced by measurements when a blade
            // actually stood.
            float plateLength = 2.2f;
            float proud = WorldBuilder.PlateProud;

            if (go == null)
            {
                // `Stand` already filed the miss. The board is not a decoy
                // here — see this method's header — because the name is the
                // content, and the lettering below runs either way.
                PlateBoard(name, at, yaw);
            }
            else
            {
                var rends = go.GetComponentsInChildren<Renderer>();
                var b = rends[0].bounds;
                foreach (var r in rends) b.Encapsulate(r.bounds);

                // `alongWall` and `outward` are axis-aligned units, so a dot
                // against an all-positive size vector picks that axis' extent
                // (signed) and `Abs` recovers it.
                float along = Mathf.Abs(Vector3.Dot(b.size, alongWall));
                float across = Mathf.Abs(Vector3.Dot(b.size, outward));
                if (across > along)
                {
                    // A quarter turn about the MOUNTING POINT rather than the
                    // model's own pivot, so the plate stays where it was hung.
                    go.transform.RotateAround(at, Vector3.up, 90f);
                    b = rends[0].bounds;
                    foreach (var r in rends) b.Encapsulate(r.bounds);
                    along = Mathf.Abs(Vector3.Dot(b.size, alongWall));
                    across = Mathf.Abs(Vector3.Dot(b.size, outward));
                    WorldBuilder.KitTally.Flagged("sign_plate_name", "blade_turned");
                }
                if (along > 0.01f) plateLength = along;
                // Half the blade's own measured thickness plus the 2.5cm of
                // clearance the primitive board gets. INHERITING THE BOARD'S
                // 0.05 WOULD BURY EVERY NAME: the blade is 0.31m deep against
                // the board's 0.05m, so the glyphs would sit inside the mesh
                // — a nameplate that cannot carry its name.
                if (across > 0.01f) proud = across / 2f + 0.025f;
            }

            // ---- the lettering, and the fit is MEASURED ------------------
            //
            // The two faces are two `Letter` calls rather than one
            // `bothSides` call ON PURPOSE: the front is created first so its
            // rendered width can be read, and the back is created afterwards
            // at whatever size that reading settled on. One implementation,
            // called twice, with the reason written down.
            float size = InkPerMetre * plateLength;
            int faces = WorldBuilder.Letter(name + "_text_front", at, text, yaw, size,
                                            WorldBuilder.PlateInk, bothSides: false,
                                            proud: proud, front: out var front);

            // WHICH OF THREE THINGS HAPPENED, because "it fitted" and "nothing
            // measured it" must not print alike (rule 3b). `text_unmeasured`
            // is a live possibility rather than a defensive branch: a TextMesh
            // generates its mesh lazily, and if the renderer has no bounds yet
            // the fit below is silently skipped and the derived start size is
            // what ships. That is the reading that would send somebody here.
            string fit = "text_unmeasured";
            var fr = front != null ? front.GetComponent<Renderer>() : null;
            float drawn = fr != null ? Mathf.Abs(Vector3.Dot(fr.bounds.size, alongWall)) : 0f;
            if (drawn > 0.001f)
            {
                // 90% of the blade, so the longest name in `StreetMap` still
                // has an end margin rather than running off the enamel.
                float room = plateLength * 0.90f;
                fit = "text_fitted";
                if (drawn > room)
                {
                    size *= room / drawn;
                    front.characterSize = size;
                    fit = "text_shrunk";
                }
            }
            WorldBuilder.KitTally.Flagged("sign_plate_name", fit);

            faces += WorldBuilder.Letter(name + "_text_back", at, text, yaw + 180f, size,
                                         WorldBuilder.PlateInk, bothSides: false,
                                         proud: proud, front: out _);

            // PAINTED means the glyphs got the depth-testing material and will
            // draw as lettering rather than as the ZTest-Always mess that put
            // garbled text over the skyline. It is NOT "a TextMesh exists":
            // that cannot fail here and a numerator that cannot fail is one
            // variable printed twice.
            //
            // AND IT IS FLAGGED ONLY FOR A BLADE THAT STOOD, WHICH IS NOT
            // FUSSINESS — IT WAS PRINTING AN IMPOSSIBILITY. `namePlatesPainted`
            // is `FlagOver(painted, sign_plate_name)`: painted flags over
            // PLACED plates. Flagging the lettered fallback board too made a
            // run with no kit model print `namePlatesPainted=2/0` — a
            // numerator above its own denominator, which is the exact shape of
            // `44 offered in one frame against 28 ever managed` that cost this
            // project an afternoon and a deleted counter. A lettered board is
            // a real and different fact, so it gets its own row rather than a
            // share of this one, and the two together still say the street
            // carries its names.
            if (faces > 0)
                WorldBuilder.KitTally.Flagged("sign_plate_name",
                    go != null ? KitDressing.FlagPainted : "board_lettered");
        }

        /// THE BLADE'S TRUE HEIGHT IN METRES — the FBX's own 6.00 units at the
        /// kit's measured 0.074 m/unit, printed by `tools/prop-dimensions.py`
        /// (4.25 x 6.00 x 19.25 units for `road-sign-object-street`). `Stand`
        /// normalises the whole model by this one figure, so the other two
        /// axes come out right without anybody hardcoding a scale factor a
        /// re-import would falsify.
        const float BladeTall = 0.44f;

        /// GLYPH HEIGHT PER METRE OF PLATE. Derived from the one lettering
        /// value in this file that has actually shipped and been looked at:
        /// the wall nameplate lettered its 2.2m board at 0.05 — the pair of
        /// numbers `PlateBoard` and the old `WallPlate` carried between them
        /// before the blade — so 0.0227 per metre.
        ///
        /// IT IS A STARTING VALUE AND NOT A BOUND, and the reason is that it
        /// HAS NEVER BEEN SEEN CARRYING A LONG NAME. `StreetMap`'s tables hold
        /// 51 street names up to eighteen characters ("Morning After Lane"),
        /// and the fit measurement above is what turns this ratio into a size
        /// that is actually known to fit. `kitFlagsBy` carries which of
        /// `text_fitted` / `text_shrunk` / `text_unmeasured` happened, per
        /// run, so the next reader sets this from a series rather than from
        /// the ratio (rule 2: ship the printer, read real runs, then choose).
        const float InkPerMetre = 0.05f / 2.2f;

        /// THE BLADE'S PAINT. A kit prop arrives wearing whatever swatch its
        /// author assigned and the noir grade desaturates everything
        /// downstream, so it is repainted through `TintFurniture` like every
        /// other kit object. The value is `StreetDressing`'s landed
        /// `BarrierWhite` — an off-white already shipped and looked at on a
        /// prop from THIS kit under THIS grade — rather than a fresh guess at
        /// what enamel should be.
        static readonly Color PlateEnamel = new Color(0.78f, 0.77f, 0.73f);

        /// THE PRIMITIVE BOARD, when the kit blade is not in the build.
        static void PlateBoard(string name, Vector3 at, float yaw)
        {
            var board = GameObject.CreatePrimitive(PrimitiveType.Cube);
            board.name = name;
            board.transform.position = at;
            board.transform.localScale = new Vector3(2.2f, 0.32f, 0.05f);
            board.transform.rotation = Quaternion.Euler(0, yaw, 0);
            board.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Plaster);
            Strip(board.GetComponent<Collider>());
        }

        static void Plate(string name, Vector3 at, string text, float yaw)
        {
            var board = GameObject.CreatePrimitive(PrimitiveType.Cube);
            board.name = name;
            board.transform.position = at;
            board.transform.localScale = new Vector3(2.6f, 0.34f, 0.06f);
            board.transform.rotation = Quaternion.Euler(0, yaw, 0);
            board.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Plaster);
            Strip(board.GetComponent<Collider>());
            Label(name + "_text", at, text, yaw, 0.055f);
        }

        /// Text on a sign, double-sided — a plate you can only read from one
        /// side is worse than no plate, because you walk round it to find out.
        ///
        /// THE BODY OF THIS MOVED TO `WorldBuilder.Letter` AND THIS IS NOW THE
        /// SHIM, because the identical idiom also existed on the shop fascia
        /// and a third copy was about to be written for the kit nameplates.
        /// Kept as a named two-argument wrapper rather than inlined at both
        /// call sites: the two callers differ only in `size`, and every other
        /// argument is a `StreetFurniture` house convention (enamel white,
        /// double-sided, 5cm proud of a 5cm board) that belongs in one place
        /// in this file rather than transcribed twice.
        ///
        /// Returns the faces that got the depth shader, 0..2, so a caller can
        /// tell "lettered" from "an object exists where lettering should be".
        static int Label(string name, Vector3 at, string text, float yaw, float size)
        {
            return WorldBuilder.Letter(name, at, text, yaw, size,
                                       WorldBuilder.PlateInk, bothSides: true,
                                       proud: WorldBuilder.PlateProud, front: out _);
        }

        static void Strip(Collider c)
        {
            if (c != null) Object.Destroy(c);
        }
    }
}
