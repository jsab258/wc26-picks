using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// M17.1. The bought body, when there is one.
    ///
    /// `CharacterRig.Bind` has had three tiers since it was written — a Humanoid
    /// Avatar, the procedural `Mannequin`, then a leaning capsule — with a note
    /// saying tier two could be deleted "when the FBX arrives". The FBX have
    /// been in the repository for days and nothing instantiated them, so tier
    /// one had never once matched.
    ///
    /// It is answered now rather than assumed: the build reports
    /// `models=44 humanoid=44 validHumanAvatar=44 clips=44`, so every FBX yields
    /// a valid human Avatar under `CharacterImport`'s settings.
    ///
    /// WHY THE PLAYER ONLY, AND NOT THE STREET. A Mixamo body is a skinned mesh
    /// of several thousand triangles; `Mannequin` is thirteen boxes. CI has no
    /// GPU and software-rasterises every frame, and the sim already spends
    /// ~297ms of a ~300ms frame in the rasteriser with the crowd it has. Putting
    /// fifty-five skinned meshes on that runner is a change whose cost I cannot
    /// predict and whose failure mode is a twenty-five-minute step timing out.
    ///
    /// So: one body, on the character in shot in every still, where it can
    /// actually be judged. The crowd keeps its boxes until there is a measured
    /// reason to change that — which is what `perFrame` and the sim's own
    /// timings will say once this has run.
    public static class RealBody
    {
        /// Whether a real body was instantiated, and why not when it was not.
        /// Read by the sim verdict — a fallback that is silent is a fallback
        /// nobody discovers, and this one is designed to be invisible.
        public static int Attached { get; private set; }
        public static string Why { get; private set; } = "not tried";

        /// `body.up` dotted with world up: 1 is standing, 0 is lying down.
        ///
        /// THE GATE THAT DID NOT EXIST. Five checks called the first bought body
        /// fine — attached, scaled, in the height range, primitive gone — while
        /// it lay on its back in the road, because every one of them asks about
        /// the body that was ADDED and none asks what it looks like. Jafar found
        /// it in the still. This is the number that would have.
        public static double Upright { get; private set; }
        public static string Orientation { get; private set; } = "not tried";

        /// HOW THE BODY IS PAINTED, counted so a run can tell the three cases
        /// apart. `Kept` is renderers that arrived with their own material,
        /// `Skinned` is head/hands/eyes, `Dressed` is everything the wardrobe
        /// covered. The build that made these necessary read `Skinned` = every
        /// renderer and `Dressed` = 0 — a naked player on a dressed street —
        /// and reported nothing at all, because a body painted entirely skin
        /// has a material on every renderer and passes every check that asks
        /// whether a material exists.
        public static int Skinned { get; private set; }
        public static int Dressed { get; private set; }
        public static int Kept { get; private set; }

        /// AND HOW MUCH OF THE BODY EACH OF THOSE ACTUALLY COVERS.
        ///
        /// The counts above are of RENDERERS, and a count cannot see
        /// proportion. `bodyDressed=1 bodySkinned=1` is the same reading
        /// whether the coat covers the torso and the skin covers the hands, or
        /// the skin covers the whole figure and the coat covers a waistband —
        /// and the noon still on 3 August shows the second one, a bare
        /// mannequin, while every number in the run said dressed. Three faults
        /// have now been found by a human opening a frame and none by a gate
        /// (rule 4); this is the one that would have caught this one.
        ///
        /// TRIANGLE AREA RATHER THAN VERTEX COUNT, because vertex share only
        /// equals surface share if the mesh is uniformly tessellated, and
        /// heads never are — a face carries a large share of a character's
        /// vertices and a small share of its skin. Area is the quantity the
        /// eye is actually judging, so it is the one to measure rather than a
        /// proxy that happens to be easier to get. Both are printed: if they
        /// disagree, the disagreement is itself the finding.
        public static double DressedAreaFraction { get; private set; }
        public static double DressedVertexFraction { get; private set; }
        public static bool CoverageRead { get; private set; }

        /// Every paintable mesh, its share of the body's surface, and which
        /// material it got — `Beta_Surface:70.4%->skin Beta_Joints:29.6%->coat`.
        /// The naked player was visible in three separate numbers and legible
        /// in none of them; this is the line that says it in words.
        public static string Parts { get; private set; } = "not tried";

        /// Is the body actually clothed? False only when coverage was READ and
        /// came back under the bound — a model whose materials all arrived
        /// textured is never measured and must not fail for it (rule 5b: the
        /// guard has to pass the case it should pass, and a bought character
        /// with its own textures is that case).
        public static bool Clothed =>
            !CoverageRead || DressedAreaFraction >= BodyParts.MinDressedArea;

        /// The skeleton as IMPORTED, before anything animates it. See the note
        /// where these are measured: this is what tells a bad import apart from
        /// a bad animation without spending a CI round trip on each guess.
        public static float BindHeadAboveHips { get; private set; }
        public static float BindHipsAboveFeet { get; private set; }
        public static bool BindPoseRead { get; private set; }

        /// The same span AFTER the body is scaled to its target height. See the
        /// note where it is taken: the bind sample alone left the scaling step
        /// unmeasured, which is precisely where a bisect must not have a gap.
        public static float ScaledHeadAboveHips { get; private set; }
        public static float ScaledHipsAboveFeet { get; private set; }
        public static bool ScaledPoseRead { get; private set; }

        /// WHICH BODY THIS PERSON HAS, and it must never change.
        ///
        /// Every `Body_*.prefab` in Resources is one bought mesh.
        /// `CharacterPrefab` writes one per FBX sitting directly in
        /// `Assets/Characters`, so the moment more than one lands the town
        /// stops being sixty people wearing one face.
        ///
        /// Chosen through `Physique.Fraction`, which is the function this
        /// project already uses to make a name mean a body — "the same name is
        /// the same body, always; a city that reshuffles its people on reload
        /// is broken in a way nobody can unsee". A different salt from the
        /// wardrobe's, or everybody in a navy coat would also share a face.
        ///
        /// SORTED, because `Resources.LoadAll` does not promise an order and
        /// an unsorted list would give the same name a different body whenever
        /// a new mesh was added — which is the reshuffle that rule forbids,
        /// arriving through the back door.
        static GameObject[] _bodies;
        public static int BodyChoices { get; private set; }

        static GameObject PickBody(string wearer)
        {
            if (_bodies == null)
            {
                var all = Resources.LoadAll<GameObject>("Characters");
                var list = new System.Collections.Generic.List<GameObject>();
                foreach (var g in all)
                    if (g != null && g.name.StartsWith("Body_")) list.Add(g);
                list.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
                _bodies = list.ToArray();
                BodyChoices = _bodies.Length;
            }
            if (_bodies.Length == 0)
                return Resources.Load<GameObject>("Characters/Body");
            double f = Ledger.Core.Physique.Fraction(wearer ?? "player", 23);
            int i = Mathf.Clamp((int)(f * _bodies.Length), 0, _bodies.Length - 1);
            return _bodies[i];
        }

        /// The mesh a renderer draws, whether it is skinned or not. One reader,
        /// because the body has both kinds and two lookups would eventually
        /// disagree about which meshes count.
        static Mesh MeshOf(Renderer r)
        {
            if (r is SkinnedMeshRenderer smr) return smr.sharedMesh;
            var mf = r != null ? r.GetComponent<MeshFilter>() : null;
            return mf != null ? mf.sharedMesh : null;
        }

        static int VertexCount(Renderer r)
        {
            var m = MeshOf(r);
            return m != null ? m.vertexCount : 0;
        }

        /// Total triangle area of a renderer's mesh, in the mesh's own units.
        ///
        /// Local space deliberately, and not world: every renderer on this body
        /// shares one root scale, so a uniform factor cancels in the FRACTION
        /// that is the only thing anybody reads. Doing it in world space would
        /// add a per-vertex transform to a loop over fifty thousand triangles
        /// for a number that comes out identical.
        static double SurfaceArea(Renderer r)
        {
            var mesh = MeshOf(r);
            if (mesh == null) return 0;
            var verts = mesh.vertices;
            var tris = mesh.triangles;
            if (verts == null || tris == null) return 0;
            double sum = 0;
            for (int i = 0; i + 2 < tris.Length; i += 3)
            {
                int a = tris[i], b = tris[i + 1], c = tris[i + 2];
                if (a >= verts.Length || b >= verts.Length || c >= verts.Length) continue;
                // Half the cross product's magnitude — the triangle's area, and
                // the only definition of "how much of this person" that does
                // not depend on how finely somebody chose to tessellate a face.
                sum += Vector3.Cross(verts[b] - verts[a], verts[c] - verts[a]).magnitude * 0.5;
            }
            return sum;
        }

        /// One reader for both samples, so the two cannot measure subtly
        /// different things. A bisect whose arms disagree proves nothing.
        static bool ReadBoneSpan(GameObject body, out float headAboveHips, out float hipsAboveFeet)
        {
            headAboveHips = hipsAboveFeet = 0f;
            var anim = body != null ? body.GetComponentInChildren<Animator>() : null;
            if (anim == null || !anim.isHuman) return false;
            var hips = anim.GetBoneTransform(HumanBodyBones.Hips);
            var head = anim.GetBoneTransform(HumanBodyBones.Head);
            var lf = anim.GetBoneTransform(HumanBodyBones.LeftFoot);
            var rf = anim.GetBoneTransform(HumanBodyBones.RightFoot);
            if (hips == null || head == null || (lf == null && rf == null)) return false;
            float sole = lf != null && rf != null
                ? Mathf.Min(lf.position.y, rf.position.y)
                : (lf != null ? lf.position.y : rf.position.y);
            headAboveHips = head.position.y - hips.position.y;
            hipsAboveFeet = hips.position.y - sole;
            return true;
        }

        public static void ResetCounters()
        {
            Attached = 0;
            Why = "not tried";
        }

        /// Put a skinned body under `host`, or return false and leave the caller
        /// to build a `Mannequin`.
        ///
        /// The prefab is written by `Editor/CharacterPrefab` at build time and
        /// carries an `Animator` whose avatar is the model's own — which is
        /// precisely what `CharacterRig.Bind` looks for.
        public static bool TryAttach(GameObject host, float targetHeightMetres = 1.8f,
                                     string wearer = "player")
        {
            if (host == null) { Why = "no host"; return false; }

            var prefab = PickBody(wearer);
            if (prefab == null)
            {
                // The likeliest cause is that the Editor step did not run, not
                // that the model is bad — and saying which saves a build.
                Why = "Resources/Characters/Body not in the build";
                return false;
            }

            var body = Object.Instantiate(prefab, host.transform);
            if (body == null) { Why = "instantiate returned null"; return false; }
            body.name = "RealBody";

            // AND THE CAPSULE GOES, which this did not do and `Mannequin.Build`
            // has always done.
            //
            // THE STILL IS HOW IT WAS FOUND, and every gate in the run said the
            // body was fine: `realBody=1`, `realBodyWhy=[ok (raw 1.90m scaled
            // x0.949)]`, `bodiesOk=True`, `height=1.58..1.90`. All true. The
            // player was still a two-metre white capsule with a pair of skin-
            // coloured arms poking out of it, because `PlayerController.Spawn`
            // builds the host from `CreatePrimitive(Capsule)` and nothing here
            // removed the mesh that came with it. The bought body was inside,
            // at exactly the same height, hidden by the thing it replaced.
            //
            // Not one gate could have caught it. Every one of them asks about
            // the body that was ADDED and none asks what is still being DRAWN —
            // so `PlayerController` now reports `playerPrimitive`, and the sim
            // gates on it.
            //
            // The instruction was eleven lines long in `Mannequin.Build`, with
            // its reasoning attached, and I wrote the parallel path without
            // reading it. That is the `persist-credentials: false` incident
            // again: the comment that would have prevented it was sitting just
            // above the code I was copying the shape of.
            //
            // The renderer, not the object — anything holding the transform
            // still holds it.
            var mesh = host.GetComponent<MeshRenderer>();
            if (mesh != null) Object.Destroy(mesh);
            var filter = host.GetComponent<MeshFilter>();
            if (filter != null) Object.Destroy(filter);
            // DOWN, NOT UP, AND THE SIGN IS THE WHOLE THING. The host's origin
            // sits at hip height — `Mannequin.HipY = -SoleBelowOrigin`, and
            // callers spawn at `ground + up * SoleBelowOrigin`. A Mixamo rig's
            // origin is at the FEET. So the body hangs 0.9m BELOW the host to
            // put its soles on the pavement; positive would float it a hip's
            // height above the street, which is precisely the kind of fault a
            // still would show and a gate would not.
            body.transform.localPosition = new Vector3(0f, -Mannequin.SoleBelowOrigin, 0f);
            body.transform.localRotation = Quaternion.identity;

            // A MATERIAL, because the model ships without one and Unity's
            // stand-in for that is bright pink. The first body on the street was
            // magenta and lying down, and the magenta is the easier half.
            // Skin-toned and flat, matching what `Mannequin` dresses its own
            // bodies in, so the two tiers do not read as different species.
            // AND THEN THE STILL SHOWED WHY THAT COMMENT WAS ONLY HALF A FIX.
            //
            // The fallback fired on EVERY renderer — the model ships with no
            // materials at all — so the player walked the street as a
            // uniformly skin-coloured figure while `wardrobe=[navy:492
            // charcoal:549 olive:267 brown:449 oxblood:100]` said the crowd was
            // dressed. Nothing was broken by the measure any gate took:
            // `realBody=1`, `playerPrimitive=False`, `bodyUp=1.000`,
            // `SceneAudit` clean with no `noMaterial` finding — because there
            // WAS a material, and it was skin.
            //
            // A person with no clothes is not a missing-material bug, which is
            // why every check built to catch missing materials passed. It is a
            // MISSING WARDROBE, and the player was the only body in the city
            // nothing dressed.
            //
            // So: skin stays the fallback for anything unpainted, and the body
            // is then DRESSED from `Core/Wardrobe` like everybody else — at a
            // named character's value rather than the crowd's, since
            // `Wardrobe.MaxValue` exists precisely so the cast stay brighter
            // than the street. `Skinned` and `Dressed` are counted so a run can
            // tell "the fallback painted everything" from "the model arrived
            // with its own materials", which the last one could not.
            var skin = AssetLibrary.Opaque(new Color(0.72f, 0.58f, 0.47f));
            // FULLY QUALIFIED, because this file deliberately has no `using
            // Ledger.Core;` — that import collides `Ledger.Core.Object`-shaped
            // names with `UnityEngine.Object` and the bare `Object.Destroy`
            // above becomes CS0104. `lint-usings.py` caught the import I nearly
            // added instead, which is a 28-minute CI round trip it just saved.
            Ledger.Core.Wardrobe.Dress(
                Ledger.Core.Physique.Fraction(wearer ?? "player", 7),
                out double ch, out double cs, out double cv);
            // The cast sit above the crowd's ceiling on purpose — Rocco 0.75,
            // Ada 0.75, Sam 0.65 — and the player is a named character.
            // `Wardrobe.MaxValue` is 0.46 and exists so nobody in the crowd
            // outshines them, so lifting off the band keeps the hue and
            // saturation the wardrobe chose while placing the value where the
            // cast live. 0.68 is under Rocco's 0.75: the protagonist should not
            // be the brightest man on his own street either.
            //
            // BUT THE LIFT IS SCALED BY SATURATION, and the stills are why.
            // A flat +0.22 is fine on denim or burgundy and ruinous on grey or
            // stone, whose saturation floor is 0.02 — lifting those to 0.68
            // produces a near-white coat, which is what `review_day1_noon` and
            // `review_day2_night` at 45c96bc actually show. It is also the
            // exact look of the white-capsule fault this project already fixed
            // once, so it would have been read as a regression in that.
            //
            // Scaling by the band's own saturation means a coloured coat gets
            // the full step and a grey one barely moves, which is how cloth
            // behaves: a bright grey is just a pale grey, while a bright navy
            // is still navy. No new constant — the multiplier is the
            // saturation the wardrobe already chose.
            float lift = 0.22f * Mathf.Clamp01((float)cs / 0.35f);
            float coatV = Mathf.Min(0.68f, (float)cv + lift);
            var coat = AssetLibrary.Opaque(Color.HSVToRGB((float)ch, (float)cs, coatV));
            Skinned = Dressed = Kept = 0;
            double coatArea = 0, totalArea = 0;
            long coatVerts = 0, totalVerts = 0;
            CoverageRead = false;

            // TWO PASSES, BECAUSE THE DECISION IS ABOUT THE MODEL AND NOT ABOUT
            // ONE NAME. `BodyParts.Assign` needs to see every paintable mesh at
            // once: a body that is a SINGLE mesh cannot be dressed part-bare,
            // and the honest answer there is a coloured mannequin rather than a
            // nude. One renderer at a time cannot know that.
            var paint = new List<Renderer>();
            foreach (var r in body.GetComponentsInChildren<Renderer>())
            {
                if (r == null) continue;
                var m = r.sharedMaterial;
                // KEEP ONLY WHAT IS ACTUALLY PAINTED, AND THE TEST IS A
                // TEXTURE RATHER THAN A NAME.
                //
                // This read `!m.name.StartsWith("Default")` and the build said
                // exactly what was wrong with it: `bodyKeptMats=2
                // bodySkinned=0 bodyDressed=0`. Both of the body's renderers
                // carry a material that is NOT called "Default…", so both were
                // kept and neither the skin nor the coat was ever applied —
                // the dressing code I shipped last cycle did not run once. The
                // pink is the model's own material.
                //
                // A NAME IS NOT EVIDENCE OF AUTHORSHIP. An untextured
                // stand-in has a name too. What distinguishes a material
                // somebody made from a placeholder is that it has a texture on
                // it, and that is a property rather than a guess.
                if (m != null && m.mainTexture != null) { Kept++; continue; }
                paint.Add(r);
            }

            // WHICH RENDERER IS SKIN AND WHICH IS COAT, FROM THE NAME — and
            // the rule now lives in Core where it has unit tests, because the
            // version that lived here was wrong for weeks and could only have
            // been caught by a 28-minute Windows round trip.
            //
            // What was wrong with it: `name.Contains("face")` matched
            // `Beta_Surface`, which is the whole body. The player was painted
            // flesh from the neck down and the coat went on the joint balls,
            // and that is the naked figure in the middle of the noon still.
            // `BodyParts.IsFlesh` compares WORDS for equality; sur-face is not
            // face, and there is a test named after it.
            var names = new string[paint.Count];
            for (int i = 0; i < paint.Count; i++) names[i] = paint[i].name;
            var isFlesh = BodyParts.Assign(names);

            var parts = new System.Text.StringBuilder();
            var areas = new double[paint.Count];
            for (int i = 0; i < paint.Count; i++)
            {
                var r = paint[i];
                bool flesh = isFlesh[i];
                r.sharedMaterial = flesh ? skin : coat;
                if (flesh) Skinned++; else Dressed++;

                // HOW MUCH OF THE PERSON THIS RENDERER IS. Measured on the
                // mesh the wardrobe just painted, so the answer cannot drift
                // from the decision it describes.
                double a = SurfaceArea(r);
                int verts = VertexCount(r);
                areas[i] = a;
                totalArea += a; totalVerts += verts;
                if (!flesh) { coatArea += a; coatVerts += verts; }
            }

            // NAME EVERY MESH, ITS SHARE AND WHICH WAY IT WENT.
            //
            // Rule 4's repair. `bodySkinned=1 bodyDressed=1 bodyCoatArea=0.296`
            // was in every verdict for as long as the player was naked, and it
            // is the correct reading of a body painted the wrong way round — it
            // simply never named the mesh, so nothing in the file connected
            // 29.6% to "the coat is on the joints". One line does:
            //
            //     bodyParts=[Beta_Surface:70.4%->skin Beta_Joints:29.6%->coat]
            //
            // and the fault is legible from the text alone, with no picture and
            // no round trip.
            for (int i = 0; i < paint.Count; i++)
            {
                double share = totalArea > 0 ? areas[i] / totalArea : 0;
                parts.Append(i == 0 ? "" : " ")
                     .Append(paint[i].name).Append(':')
                     .Append((share * 100.0).ToString("0.0")).Append("%->")
                     .Append(isFlesh[i] ? "skin" : "coat");
            }
            Parts = parts.ToString();

            // TWO MEASUREMENTS, TWO GATES, and the first run is why.
            //
            // These used to share one `if (totalArea > 0)`, so when the mesh
            // turned out to be non-readable — `mesh.vertices` returns an EMPTY
            // ARRAY rather than throwing — the area came back zero and took the
            // vertex fraction down with it. Both printed 0.000, which is
            // exactly what a coat covering nothing looks like.
            //
            // `vertexCount` is metadata and works on a non-readable mesh, so it
            // would have answered on its own. One condition guarding two
            // independent facts is the same fault as a reset that clears half a
            // class's counters: the half it forgets looks deliberate.
            //
            // And -1 rather than 0 for "not measured", because a fraction of
            // zero is a legitimate reading and must not be confused with the
            // absence of one.
            DressedAreaFraction = totalArea > 0 ? coatArea / totalArea : -1;
            DressedVertexFraction = totalVerts > 0 ? (double)coatVerts / totalVerts : -1;
            CoverageRead = totalArea > 0 && totalVerts > 0;

            // WHICH WAY UP, PRINTED. Setting the instantiated root's rotation to
            // identity above corrects nothing if the axis conversion sits on a
            // node BELOW it, which is what a Z-up FBX imported without
            // `bakeAxisConversion` leaves behind. `CharacterImport` now bakes it;
            // this reports the outcome rather than trusting that it took, and
            // says which transform any residual rotation is on.
            var childRot = body.transform.childCount > 0
                ? body.transform.GetChild(0).localRotation.eulerAngles
                : Vector3.zero;
            Upright = Vector3.Dot(body.transform.up, Vector3.up);
            Orientation = $"root={body.transform.localRotation.eulerAngles} "
                          + $"child0={childRot} up.y={Upright:0.000}";

            // THE BIND POSE, MEASURED BEFORE ANYTHING ANIMATES IT.
            //
            // The run reports `headAboveHips=-0.130 hipsAboveFeet=-0.778` — the
            // player is upside down — while `bodyUp=1.000` says the root is
            // perfectly upright. Two hypotheses fit that equally well and they
            // have opposite fixes:
            //
            //   IMPORT   `bakeAxisConversion = true` is wrong for these files.
            //            It was set because a body lay on its back, and the
            //            evidence that it worked was `bodyUp` going to 1.000 —
            //            which reads the ROOT and could never have seen the
            //            skeleton. If Mixamo's FBX were already Y-up, baking a
            //            conversion would have introduced the flip rather than
            //            removed it, and I would have confirmed the fix with an
            //            instrument that cannot see the fault.
            //   ANIMATE  the import is fine and something downstream — a clip,
            //            the avatar binding, or `CharacterRig`'s own solve — is
            //            driving the bones inverted.
            //
            // Guessing costs a 28-minute round trip per guess. Measuring the
            // BIND pose here, before a single frame has animated, separates
            // them in ONE: if the T-pose is already inverted it is the import,
            // and if the T-pose is upright while the run is not, it is
            // everything after.
            BindPoseRead = false;
            if (ReadBoneSpan(body, out float bh, out float bf))
            {
                BindHeadAboveHips = bh;
                BindHipsAboveFeet = bf;
                BindPoseRead = true;
            }

            // SCALE FROM THE BOUNDS, NOT FROM A CONSTANT. Mixamo's own scale
            // depends on how the file was exported, and `useFileScale` respects
            // whatever the FBX declares — which is the honest setting and also
            // the one that leaves the actual height unknown until it is
            // measured. `Mannequin` builds people 1.58-1.90m and the sim gates
            // on that range, so a body arriving at 100x would fail a gate rather
            // than quietly tower over the street.
            float measured = HeightOf(body);
            if (measured > 0.01f)
            {
                float k = targetHeightMetres / measured;
                body.transform.localScale = Vector3.one * k;
                Why = $"ok (raw {measured:0.00}m scaled x{k:0.000})";
            }
            else
            {
                Why = $"ok (no renderer bounds; left at file scale)";
            }

            // AND THE SAME MEASUREMENT AGAIN, AFTER SCALING, because the last
            // bisect had a hole in exactly this shape.
            //
            // The bind sample above is taken at instantiate, BEFORE this scale
            // is applied. It read +0.56 / +0.96 — upright — and I reported
            // that as "the import is innocent". It only ever showed the body
            // innocent up to that LINE. Everything between it and the
            // Animator was unmeasured, and the scale sits right in the gap.
            //
            // So the stages are now fully bracketed: bind (post-instantiate),
            // scaled (here), pre-solve (top of `CharacterRig.LateUpdate`, so
            // after the Animator), and post-solve. Whichever adjacent pair
            // disagrees is the stage that inverts the body, and there is
            // nowhere left for it to hide.
            if (ReadBoneSpan(body, out float sh, out float sf))
            {
                ScaledHeadAboveHips = sh;
                ScaledHipsAboveFeet = sf;
                ScaledPoseRead = true;
            }

            Attached++;
            StageNoClipTwin(prefab, host);
            return true;
        }

        /// THE LAST TWO SUSPECTS, SEPARATED BY A BODY THAT IS HANDED NO
        /// ANIMATION AT ALL.
        ///
        /// `importerRan=44` closed the import: the postprocessor runs on every
        /// model, so the bake experiment that came back identical to three
        /// decimals really was an experiment, and the bake really is not the
        /// variable. Bind pose upright, scaled pose upright, everything after
        /// the Animator inverted. Two suspects are left and they need opposite
        /// fixes:
        ///
        ///   the CLIP's curves are inverted   -> reauthor or reimport the clips
        ///   the AVATAR's mapping is inverted -> rebuild the human description
        ///
        /// The bind-pose reading cannot tell them apart, because a disabled
        /// Animator leaves the bones exactly where the bind pose put them —
        /// which is the number already measured, and it is upright. The
        /// distinguishing case is an Animator that is ENABLED and BOUND to the
        /// avatar but has no clip to play: it evaluates the avatar's own
        /// default humanoid pose through muscle space, so the avatar does all
        /// the work and no clip contributes anything.
        ///
        ///   twin upright  -> the avatar maps correctly and the clip inverts
        ///   twin inverted -> the avatar inverts, and the clip is innocent
        ///
        /// A SEPARATE, HIDDEN INSTANCE rather than a change to the player. I
        /// have twice made the body the subject of a test and twice had to ask
        /// whether the test moved it; a probe that touches the thing it
        /// measures cannot answer a question about what moved it. This one is
        /// disabled for rendering, parented off to the side, and never solved
        /// by `CharacterRig` — it exists for one reading and costs one skinned
        /// mesh for the length of the run.
        static void StageNoClipTwin(GameObject prefab, GameObject host)
        {
            if (prefab == null || host == null || TwinRead) return;
            var twin = Object.Instantiate(prefab, host.transform);
            twin.name = "NoClipTwin";
            twin.transform.localPosition = new Vector3(0f, -40f, 0f);
            foreach (var r in twin.GetComponentsInChildren<Renderer>()) r.enabled = false;
            // Any `CharacterRig` on the twin would solve it and contaminate the
            // very pose being read — the same reason the reading is taken before
            // the solve on the real body.
            foreach (var rig in twin.GetComponentsInChildren<CharacterRig>()) Object.Destroy(rig);

            var anim = twin.GetComponentInChildren<Animator>();
            if (anim == null) { TwinWhy = "no animator on the twin"; return; }
            // ENABLED AND BOUND, WITH NOTHING TO PLAY. Clearing the controller
            // rather than disabling the Animator is the whole experiment: a
            // disabled Animator reports the bind pose, which is already known
            // and already upright.
            anim.runtimeAnimatorController = null;
            anim.enabled = true;
            TwinHuman = anim.avatar != null && anim.avatar.isHuman;
            TwinWhy = TwinHuman ? "bound, no controller" : "avatar not human";
            _twin = twin;
        }

        static GameObject _twin;

        /// Read once, late, from the sim — the Animator needs a frame to
        /// evaluate before there is anything to measure, and reading in the
        /// same frame it was created would report the bind pose and quietly
        /// answer the wrong question.
        public static void ReadNoClipTwin()
        {
            if (_twin == null || TwinRead) return;
            if (ReadBoneSpan(_twin, out float h, out float f))
            {
                TwinHeadAboveHips = h;
                TwinHipsAboveFeet = f;
                TwinRead = true;
            }
        }

        public static float TwinHeadAboveHips { get; private set; }
        public static float TwinHipsAboveFeet { get; private set; }
        public static bool TwinRead { get; private set; }
        public static bool TwinHuman { get; private set; }
        public static string TwinWhy { get; private set; } = "not staged";

        /// World height of everything renderable under `go`. Uses renderer
        /// bounds rather than the transform, because a rig's root transform says
        /// nothing about how tall the mesh on it is.
        static float HeightOf(GameObject go)
        {
            var renderers = go.GetComponentsInChildren<Renderer>();
            if (renderers == null || renderers.Length == 0) return 0f;
            var bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++) bounds.Encapsulate(renderers[i].bounds);
            return bounds.size.y;
        }
    }
}
