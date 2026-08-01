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
        public static bool TryAttach(GameObject host, float targetHeightMetres = 1.8f)
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
            // DOWN, NOT UP, AND THE SIGN IS THE WHOLE THING. The host's origin
            // sits at hip height — `Mannequin.HipY = -SoleBelowOrigin`, and
            // callers spawn at `ground + up * SoleBelowOrigin`. A Mixamo rig's
            // origin is at the FEET. So the body hangs 0.9m BELOW the host to
            // put its soles on the pavement; positive would float it a hip's
            // height above the street, which is precisely the kind of fault a
            // still would show and a gate would not.
            body.transform.localPosition = new Vector3(0f, -Mannequin.SoleBelowOrigin, 0f);
            body.transform.localRotation = Quaternion.identity;

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
