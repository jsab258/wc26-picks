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

            var prefab = Resources.Load<GameObject>("Characters/Body");
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
            // outshines them, so lifting by a fixed step off the band keeps the
            // hue and saturation the wardrobe chose while placing the value
            // where the cast live. 0.68 is under Rocco's 0.75, not a tuned
            // number: the protagonist should not be the brightest man on his
            // own street either.
            float coatV = Mathf.Min(0.68f, (float)cv + 0.22f);
            var coat = AssetLibrary.Opaque(Color.HSVToRGB((float)ch, (float)cs, coatV));
            Skinned = Dressed = Kept = 0;
            foreach (var r in body.GetComponentsInChildren<Renderer>())
            {
                if (r == null) continue;
                var m = r.sharedMaterial;
                // Only where nothing was authored. A model that DOES arrive with
                // materials keeps them — this is a fallback, not a repaint.
                if (m != null && !m.name.StartsWith("Default", System.StringComparison.Ordinal))
                { Kept++; continue; }

                // WHICH RENDERER IS SKIN AND WHICH IS COAT, FROM THE NAME.
                //
                // Mixamo names its submeshes, and head/hands/eyes are the parts
                // that should stay flesh. Anything else is body, and body wears
                // a coat. Read off the name rather than off an index, because
                // an index would silently mean something different the first
                // time a different model is bought — and this project has been
                // bitten by exactly that with the hand lookup.
                string n = r.name.ToLowerInvariant();
                bool flesh = n.Contains("head") || n.Contains("hand")
                          || n.Contains("eye") || n.Contains("face");
                r.sharedMaterial = flesh ? skin : coat;
                if (flesh) Skinned++; else Dressed++;
            }

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

            Attached++;
            return true;
        }

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
