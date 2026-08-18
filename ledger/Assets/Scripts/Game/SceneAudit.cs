using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace Ledger.Game
{
    /// WHAT MUST BE TRUE OF WHAT IS ON SCREEN — the check nobody wrote.
    ///
    /// THREE FAULTS IN ONE DAY, ALL FOUND BY A HUMAN OPENING A JPEG, none by a
    /// gate:
    ///
    ///   a hand lookup that could only see one body tier   (drawn=0)
    ///   a white capsule drawn over the bought body        (five gates green)
    ///   that body lying flat on its back, and magenta     (five gates green)
    ///
    /// The last two are the damning ones. `realBody=1`, `bodiesOk=True`,
    /// `height=1.58..1.90` — every clause true, every clause about the thing
    /// that was ADDED, and not one about what the frame LOOKS like. Each fault
    /// became a number only AFTER somebody saw it, which makes the process a
    /// human eye with a very long feedback loop.
    ///
    /// CLAUDE.md rule 4 already says to write a `page_check.py` equivalent for
    /// any new deliverable. `game-design/sim-shots/` has been the deliverable
    /// for a day and nobody wrote one.
    ///
    /// WHY IN-ENGINE AND NOT IMAGE ANALYSIS. A JPEG has a resolution, a
    /// compression artefact and a palette, and this project has already
    /// condemned four correct things by reading one. The sim has the SCENE
    /// GRAPH: it can ask whether a renderer has a material rather than whether
    /// some pixels look pink, and get an answer that is true rather than
    /// probable. Every check below is a statement about objects, not colours.
    ///
    /// THE POINT IS THE LIST, NOT ANY ONE ENTRY. These are the invariants that
    /// were violated while the build was green, plus the neighbours of each —
    /// and when the next still shows something wrong, the fix is a line here,
    /// not a note to look harder next time.
    public static class SceneAudit
    {
        /// One class of fault, its count, and the first example by name.
        public class Finding
        {
            public string Kind;
            public int Count;
            public string First = "";
        }

        /// Faults that mean the frame is WRONG, not merely unusual. `bodiesOk`
        /// and the sim's own gate read this; anything listed here failing is a
        /// red build.
        public static readonly string[] Fatal =
        {
            "noMaterial", "errorShader", "nanTransform", "absurdScale", "buried",
        };

        public static List<Finding> Findings { get; private set; } = new List<Finding>();

        /// Every fatal class at zero.
        public static bool Clean
        {
            get
            {
                foreach (var f in Findings)
                    foreach (var k in Fatal)
                        if (f.Kind == k && f.Count > 0) return false;
                return true;
            }
        }

        static void Note(Dictionary<string, Finding> into, string kind, string who)
        {
            if (!into.TryGetValue(kind, out var f))
            {
                f = new Finding { Kind = kind, First = who };
                into[kind] = f;
            }
            f.Count++;
        }

        /// Walk everything renderable once and report.
        ///
        /// ONCE, not per frame: this is a few thousand `GetComponent`-free
        /// property reads over the whole scene, which is cheap enough to run at
        /// a known moment and far too expensive to run at sixty hertz. The sim
        /// calls it after the world is built and dressed, which is the only
        /// point at which "what is on screen" is a settled question.
        public static void Run(GameObject playerHost)
        {
            var found = new Dictionary<string, Finding>();
            var renderers = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None);
            int seen = 0;
            // ZEROED PER PASS, because these are static and `Run` is called
            // more than once. Accumulating would report the sum over every
            // audit the run ever did and read exactly like a scene three times
            // heavier than it is — a number that is wrong in the direction that
            // makes you cut the cast.
            SkinnedRenderers = SkinnedBones = SkinnedVerts = 0;

            foreach (var r in renderers)
            {
                if (r == null || !r.enabled) continue;
                seen++;
                var t = r.transform;

                // MISSING MATERIAL. The bought body arrived with no material and
                // Unity drew it in its stand-in colour; the still looked like a
                // deliberate art choice until somebody asked. Nothing else in
                // this project renders without a material, so any hit is a bug.
                var mat = r.sharedMaterial;
                if (mat == null) { Note(found, "noMaterial", r.name); }
                else if (mat.shader == null || mat.shader.name == "Hidden/InternalErrorShader")
                    Note(found, "errorShader", r.name);

                // NaN ANYWHERE IN A TRANSFORM. A single NaN propagates through
                // every parent-child multiply it touches and takes a limb, then
                // a body, then a district with it — and it renders as nothing at
                // all, which looks exactly like a culling bug.
                var p = t.position;
                if (float.IsNaN(p.x) || float.IsNaN(p.y) || float.IsNaN(p.z)
                    || float.IsInfinity(p.x) || float.IsInfinity(p.y) || float.IsInfinity(p.z))
                { Note(found, "nanTransform", r.name); continue; }

                // ABSURD SCALE. `useFileScale` respects whatever an FBX
                // declares, and a Mixamo body at centimetre scale is a hundred
                // times too big. Bounded loosely on purpose — this is looking
                // for a factor of a hundred, not for a design opinion.
                //
                // EVERY AXIS, NOT ANY AXIS, and the numbers are unchanged.
                // This asked whether the LARGEST axis exceeded 100, and a road
                // is legitimately 150m long and 15mm thick — so it fired on
                // `Road_150` and on the yellow kerb lines, 7 times, in ALL
                // ELEVEN landed runs, and the only names it has ever produced
                // are `Road_*` and `Yellow_*`. It has never once caught a real
                // fault while sitting in `Fatal` and holding `clean=False`
                // permanently, which is how a red gate teaches everybody to
                // read red as noise — and it hid whether the rest of this
                // audit had anything to say.
                //
                // The fault being hunted is a UNIT MISMATCH, which is UNIFORM
                // by construction: a centimetre-scale import is a hundred
                // times too big on all three axes at once. A road is absurd on
                // exactly one. So the quantifier moves from any to every and
                // the bounds stay where they were — no threshold was loosened,
                // and the edge case at exactly 100 behaves as it always did.
                var s = t.lossyScale;
                float big = Mathf.Max(Mathf.Abs(s.x), Mathf.Max(Mathf.Abs(s.y), Mathf.Abs(s.z)));
                float small = Mathf.Min(Mathf.Abs(s.x), Mathf.Min(Mathf.Abs(s.y), Mathf.Abs(s.z)));
                if (small > 100f || big < 0.0005f) Note(found, "absurdScale", r.name);

                // BURIED. Something entirely below the pavement is either
                // mispositioned or the ground moved under it. The ground plane
                // itself sits at y=0 and is excluded by its own name.
                if (r.bounds.max.y < -0.5f && r.name != "Ground")
                    Note(found, "buried", r.name);

                // WHAT A CHARACTER COSTS, IN THE UNITS THAT TRAVEL.
                //
                // The cast tiering has been bounded from the design side only:
                // `Recurrence` says how many distinct faces a day the town
                // produces and `Density` says the witness engine needs about
                // twenty near an event, and nothing at all says what the
                // machine allows. I was one step from proposing a cast size on
                // half the evidence.
                //
                // This runner cannot answer the other half in milliseconds —
                // it has no GPU and software-rasterises everything, so a
                // skinning time measured here describes a software rasteriser
                // and would be quoted for a year and wrong on every real
                // machine. Bones and vertices are not like that. They are what
                // the mesh actually is, they are identical on any hardware, and
                // they are the input any GPU estimate needs. So count those,
                // and let the millisecond question wait for a machine that can
                // answer it honestly.
                var skin = r as SkinnedMeshRenderer;
                if (skin != null)
                {
                    SkinnedRenderers++;
                    if (skin.bones != null) SkinnedBones += skin.bones.Length;
                    var mesh = skin.sharedMesh;
                    if (mesh != null) SkinnedVerts += mesh.vertexCount;
                }
            }

            // THE PLAYER, SPECIFICALLY, because it is the one object in every
            // still and the one all three faults landed on.
            //
            // PASSED IN, not fetched from a singleton: `GameController` has no
            // `Instance` and I nearly wrote one against it from memory. The sim
            // already holds the player and is the only caller.
            var host = playerHost;
            if (host != null)
            {
                // TWO BODIES IS THE CAPSULE FAULT IN ITS GENERAL FORM. It was a
                // MeshRenderer left on the host that time; next time it will be
                // a second prefab, or a mannequin built beside a real body.
                // Counting visible body roots catches the class rather than the
                // instance.
                int bodies = 0;
                if (host.GetComponent<MeshRenderer>() != null) bodies++;
                if (host.GetComponent<Mannequin>() != null) bodies++;
                var real = host.transform.Find("RealBody");
                if (real != null) bodies++;
                if (bodies != 1) Note(found, "playerBodies", $"{bodies} on {host.name}");

                // UPRIGHT AND ON THE GROUND. `RealBody.Upright` covers the
                // bought body; this covers the host itself, which is what the
                // camera follows and what `CharacterRig`'s capsule branch
                // compounds a lean onto when no skeleton bound.
                if (Vector3.Dot(host.transform.up, Vector3.up) < 0.9f)
                    Note(found, "playerTilted", $"up.y={host.transform.up.y:0.00}");
                if (host.transform.position.y < -2f || host.transform.position.y > 20f)
                    Note(found, "playerOffGround", $"y={host.transform.position.y:0.0}");
            }

            var list = new List<Finding>(found.Values);
            list.Sort((a, b) => b.Count.CompareTo(a.Count));
            Findings = list;
            Renderers = seen;
        }

        /// How many renderers the audit actually looked at.
        ///
        /// PRINTED BECAUSE ZERO FINDINGS FROM ZERO RENDERERS IS THE FAILURE
        /// MODE. An audit that silently walked nothing reports a perfectly clean
        /// scene, which is the same shape as the checker nobody has watched
        /// fire — and this project has shipped that twice.
        public static int Renderers { get; private set; }

        /// The geometric load one frame is carrying, per skinned character.
        /// Totals rather than averages, because the average is recoverable from
        /// the total and the count while the reverse is not — and because a
        /// single 40,000-vertex body among thirty cheap ones is exactly the
        /// thing an average would hide.
        public static int SkinnedRenderers { get; private set; }
        public static int SkinnedBones { get; private set; }
        public static int SkinnedVerts { get; private set; }

        /// WHAT IS ACTUALLY STANDING NEXT TO THE PLAYER, biggest first.
        ///
        /// WHY. `review_day2_night.jpg` has a large glowing yellow cube
        /// floating at the player's chest, dead centre of frame. It is
        /// unmistakably wrong and I cannot tell from the picture what it is —
        /// the candidates are a courier satchel drawn as a held object, a
        /// dispatch marker (wrong colour and half the height, but markers move),
        /// a detached window quad, or a lamp housing.
        ///
        /// Rule 4, in the half people skip: a picture is excellent evidence
        /// that something is WRONG and poor evidence of WHAT. Four reversals in
        /// one night came from acting on the second half — three textures and a
        /// bench condemned off a JPEG and every one of them correct. So this
        /// does not guess. It names the objects, with their size, and the next
        /// verdict says which one it is in one round trip instead of three.
        ///
        /// FOUR metres, not two, and sampled at SHOT time rather than at the
        /// night measurement. The two-metre version came back with the player's
        /// own two meshes and six nameplates and no cube at all — which is a
        /// true answer about a different instant and a smaller sphere. Exactly
        /// the mistake the speech-bubble counter made in the same hour: an
        /// instrument that samples when nothing is happening reports that
        /// nothing happens.
        ///
        /// A glowing object also marks itself with a star, because "forty
        /// things are near the player" is not an answer and the thing being
        /// hunted is LIT.
        public static string Near(Vector3 where, float metres = 4f)
        {
            var found = new List<(string name, float size, float dist, bool glows)>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (r == null || !r.enabled) continue;
                float d = Vector3.Distance(r.bounds.center, where);
                if (d > metres) continue;
                var e = r.bounds.size;
                // AND WHETHER IT GLOWS, because the thing being hunted is a
                // LIT cube and "there are forty objects near the player" is not
                // an answer. An emissive marker in a list of ordinary geometry
                // identifies itself.
                var m = r.sharedMaterial;
                bool glows = m != null && m.IsKeywordEnabled("_EMISSION");
                found.Add((r.name, Mathf.Max(e.x, Mathf.Max(e.y, e.z)), d, glows));
            }
            found.Sort((a, b) => b.size.CompareTo(a.size));
            var sb = new StringBuilder("SceneAudit: near[");
            int n = 0;
            foreach (var f in found)
            {
                if (n++ >= 8) { sb.Append(" …"); break; }
                sb.Append(n == 1 ? "" : " ").Append(f.name)
                  .Append(':').Append(f.size.ToString("0.00")).Append('m')
                  .Append('@').Append(f.dist.ToString("0.0"))
                  .Append(f.glows ? "*" : "");
            }
            return sb.Append("] of ").Append(found.Count).ToString();
        }

        public static string Report()
        {
            var sb = new StringBuilder();
            sb.Append("SceneAudit: renderers=").Append(Renderers)
              .Append(" skinned=").Append(SkinnedRenderers)
              .Append(" skinnedBones=").Append(SkinnedBones)
              .Append(" skinnedVerts=").Append(SkinnedVerts)
              .Append(" clean=").Append(Clean);
            // THE COUNT ALWAYS, THE DETAIL WHEN THERE IS ANY. This printed
            // `findings=none` on a clean scene and DROPPED THE KEY ENTIRELY
            // the moment it had something to say — so the verdict-key guard
            // reported "VERDICT KEYS GONE: findings" for a report that was
            // working perfectly, and a reader grepping `findings=` saw
            // nothing exactly when there was something to see. A key that
            // disappears when the news is bad is the inverse of rule 3b: not
            // a zero without a denominator, but a denominator that leaves
            // when the numerator arrives.
            sb.Append(" findings=").Append(Findings.Count);
            if (Findings.Count == 0) { sb.Append(" findingKinds=none"); return sb.ToString(); }
            foreach (var f in Findings)
                sb.Append(' ').Append(f.Kind).Append('=').Append(f.Count)
                  .Append("[").Append(f.First).Append("]");
            return sb.ToString();
        }
    }
}
