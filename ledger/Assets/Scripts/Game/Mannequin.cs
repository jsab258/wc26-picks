using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// A BODY, BUILT FROM PRIMITIVES, so the rig has something to move today
    /// (the-gap.md §3b).
    ///
    /// Every person in this city is a capsule. `Core/Rig` computes a gait, a
    /// lean, a breath, a limp, a look-split and two-bone IK — and all of it
    /// has been driving a transform, because the skeleton it was written for
    /// arrives with a Mixamo download that is not mine to make.
    ///
    /// So the skeleton is built here instead. Ten boxes and a sphere, in a
    /// real joint hierarchy, articulated by the same functions the bought
    /// characters will use. It will not be mistaken for a person. It will be
    /// unmistakably A PERSON WALKING, which a capsule sliding along the
    /// ground never is — and the difference between those two is most of what
    /// makes a street feel populated.
    ///
    /// It is also not throwaway. The bones are the contract: `CharacterRig`
    /// binds to an Avatar instead of to this, drives the identical joints with
    /// the identical numbers, and nothing downstream of it changes.
    ///
    /// **"AND THIS CLASS STOPS BEING INSTANTIATED" WAS THE WRONG PREDICTION,
    /// and it has been wrong since the FBX landed.** Both tiers are live at
    /// once and will be for a long time: the player has a bought skeleton and
    /// sixty-seven mannequins are the crowd, because a skinned mesh per walker
    /// has never been costed on a GPU-less runner. `CharacterRig.Bind` already
    /// says so in its own note — "it read as though the day tier one started
    /// matching was the day tier two stopped existing" — and this file was
    /// still promising the opposite one directory away.
    ///
    /// It matters beyond tidiness: a class believed to be on its way out does
    /// not get looked at, and this one is what sixty-seven of the sixty-eight
    /// bodies in every screenshot are made of.
    [DisallowMultipleComponent]
    public class Mannequin : MonoBehaviour
    {
        // Proportions, metres, for a body 1.8m tall standing with its
        // transform origin at the middle — which is where Unity's capsule
        // puts it and therefore where every caller already expects it.
        public const float ThighLength = 0.44f;
        public const float ShinLength = 0.42f;
        /// Hip joint to thigh joint, and ankle joint to the bottom of the sole.
        public const float HipToThigh = 0.04f;
        public const float AnkleToSole = 0.065f;

        /// WHERE THE FEET ARE, and the number everything vertical is derived
        /// FROM rather than checked against.
        ///
        /// The player's CharacterController is 1.8m tall centred on the
        /// transform, so its feet are here and the ground contact the whole
        /// game already assumes is here. Picking a hip height and hoping is
        /// how a city ends up with everyone shin-deep in the pavement — which
        /// is what the first version of this file did, by 6.5cm, because a
        /// capsule's bottom is at -1.0 and a controller's is at -0.9 and
        /// nothing had ever had to agree with both.
        public const float SoleBelowOrigin = 0.90f;

        /// Solved, not chosen.
        public const float HipY = -SoleBelowOrigin
            + HipToThigh + ThighLength + ShinLength + AnkleToSole;
        public const float ChestRise = 0.25f;
        public const float NeckRise = 0.28f;
        public const float HeadRise = 0.12f;
        public const float UpperArmLength = 0.28f;
        public const float ForearmLength = 0.26f;
        public const float ShoulderHalfWidth = 0.19f;
        public const float HipHalfWidth = 0.095f;

        public Transform Hips, Chest, Neck, Head;
        public Transform LThigh, LShin, LFoot, RThigh, RShin, RFoot;
        public Transform LUpperArm, LForearm, RUpperArm, RForearm;

        /// This body's proportions. Public so the rig can read the gait bias
        /// and so the sim gate can prove a crowd is not thirty of one person.
        public Physique Shape { get; private set; }

        /// Build a body onto `host`, replacing whatever primitive mesh it was
        /// wearing. The host keeps its collider, its controller and its
        /// scripts — only the visible shape changes.
        ///
        /// (This paragraph was stacked on top of `Shape`'s own doc comment, so
        /// C# attached it there and this function had none. Harmless to the
        /// compiler and not to a reader, who got "build a body onto host" as
        /// the description of a property.)
        public static Mannequin Build(GameObject host, Color skin, Color cloth, string who = null)
        {
            if (host == null) return null;
            var existing = host.GetComponent<Mannequin>();
            // ASSEMBLED, NOT MERELY PRESENT — and the distinction is the whole
            // of what makes a runtime body swap safe.
            //
            // Unity defers `Destroy` to the end of the frame, so a component
            // torn down and rebuilt in one frame is still found by
            // `GetComponent` here. The old `if (existing != null) return` would
            // hand back the husk and the walker would be INVISIBLE — no
            // mannequin, no skinned body, and nothing in this project measures
            // invisibility. So `Teardown` leaves the component in place and
            // drops its pieces, and this asks whether the pieces are there.
            if (existing != null && existing.Assembled) return existing;

            // The capsule mesh goes. Its renderer, not the object — anything
            // holding a reference to the transform still has one.
            var own = host.GetComponent<MeshRenderer>();
            if (own != null) Destroy(own);
            var ownMesh = host.GetComponent<MeshFilter>();
            if (ownMesh != null) Destroy(ownMesh);

            var m = existing != null ? existing : host.AddComponent<Mannequin>();
            m.enabled = true;
            m.Shape = Physique.For(string.IsNullOrEmpty(who) ? host.name : who);
            m.Assemble(skin, cloth);
            // The contact blob rides the HOST, not the mannequin's pieces, so
            // it survives Teardown and the tier swap to a skinned body —
            // every walker passes through here at least once, which makes
            // this the one attach site that covers the whole street. The
            // ground sits SoleBelowOrigin under the host origin.
            BlobShadow.Attach(host, -SoleBelowOrigin);
            return m;
        }

        /// Is there a body under this component, or only the component?
        ///
        /// `Hips` is the test rather than a bool, because a flag is a second
        /// record of the same fact and the two drift — the shape this project
        /// has already paid for in the label set and the walker body count.
        public bool Assembled => Hips != null;

        /// Take the mannequin's pieces off and leave the host ready for a
        /// skinned body, without destroying the component.
        ///
        /// THE COMPONENT STAYS ON PURPOSE. Destroying it and adding another in
        /// the same frame leaves two on the object — Unity's `Destroy` is
        /// deferred, so `AddComponent` runs while the first is still there and
        /// `GetComponent` afterwards may return either. Keeping one and
        /// emptying it has neither problem and is less code.
        ///
        /// Deactivated before destroying for the same reason `RealBody.Detach`
        /// does it: end-of-frame destruction means the old body renders through
        /// the frame the new one is built in.
        public static void Teardown(GameObject host)
        {
            var m = host != null ? host.GetComponent<Mannequin>() : null;
            if (m == null || !m.Assembled) return;
            // REACHED THROUGH `Hips`, NOT BY `Find("Body")`. A destroyed child
            // survives to the end of the frame and `Transform.Find` returns
            // INACTIVE children, so a name lookup here can hand back the corpse
            // of the body this method just deactivated and leave the live one
            // standing. The joint chain cannot: `Hips.parent` is by
            // construction the wrapper this mannequin actually built.
            var body = m.Hips.parent;
            if (body != null && body != m.transform)
            {
                body.gameObject.SetActive(false);
                Destroy(body.gameObject);
            }
            // EVERY JOINT NULLED, because `CharacterRig` binds to these and a
            // stale `Hips` pointing at a destroyed transform is the one thing
            // that would make `Assembled` lie in the direction that costs a
            // body.
            m.Hips = m.Chest = m.Neck = m.Head = null;
            m.LThigh = m.LShin = m.LFoot = m.RThigh = m.RShin = m.RFoot = null;
            m.LUpperArm = m.LForearm = m.RUpperArm = m.RForearm = null;
            m.enabled = false;
        }

        void Assemble(Color skin, Color cloth)
        {
            var skinMat = Mat(skin);
            var clothMat = Mat(cloth);

            // HEIGHT scales the whole body; BREADTH widens it without making
            // it taller. Applied on a single wrapper transform rather than by
            // rewriting every offset, so the joint hierarchy below stays the
            // authored one and matches the Mixamo skeleton it will be swapped
            // for.
            //
            // The wrapper is also LIFTED, because scaling a body scales the
            // distance from its origin to its soles: a 1.56m person hung off
            // an origin authored for 1.80m floats 9cm, and a 1.93m one is
            // buried. `Physique.SoleOffset` is that arithmetic and it exists
            // because the last vertical-offset bug in this file cost 6.5cm
            // and a screenshot to find.
            float scale = (float)Physique.HeightScale(Shape);
            var body = Joint("Body", transform,
                new Vector3(0, SoleBelowOrigin - (float)Physique.SoleOffset(Shape, SoleBelowOrigin), 0));
            // BREADTH ON X ONLY, and this is not an aesthetic call. Every
            // limb swings about its LOCAL X axis, in the YZ plane — so a
            // parent scaled differently in Y and Z shears each limb as it
            // rotates, stretching a leg by up to a fifth at the extremes of
            // its stride. Width is the x axis; depth staying uniform is both
            // correct and free of that.
            body.localScale = new Vector3(scale * (float)Shape.Breadth, scale, scale);

            Hips = Joint("Hips", body, new Vector3(0, HipY, 0));
            Box(Hips, "Pelvis", new Vector3(0, -0.05f, 0), new Vector3(0.30f, 0.16f, 0.20f), clothMat);

            Chest = Joint("Chest", Hips, new Vector3(0, ChestRise, 0));
            Box(Chest, "Torso", new Vector3(0, -0.06f, 0), new Vector3(0.36f, 0.34f, 0.22f), clothMat);

            Neck = Joint("Neck", Chest, new Vector3(0, NeckRise, 0));
            Box(Neck, "NeckMesh", new Vector3(0, 0.03f, 0), new Vector3(0.09f, 0.08f, 0.09f), skinMat);

            Head = Joint("Head", Neck, new Vector3(0, HeadRise, 0));
            // The head carries its own size, and cancels breadth on the way
            // — a broad person whose head widened by the same factor reads as
            // a caricature, and the head is the part of a silhouette a viewer
            // measures the rest against.
            Head.localScale = new Vector3(
                (float)Shape.HeadScale / Mathf.Max(0.01f, (float)Shape.Breadth),
                (float)Shape.HeadScale, (float)Shape.HeadScale);
            Ball(Head, "Skull", new Vector3(0, 0.04f, 0), 0.20f, skinMat);
            // A nose. One box, and it is the entire reason a head reads as
            // facing somewhere rather than as a ball on a stick — which
            // matters here more than anywhere, because the look-split is the
            // most visible thing the rig does.
            Box(Head, "Face", new Vector3(0, 0.03f, 0.09f), new Vector3(0.05f, 0.05f, 0.06f), skinMat);
            // EYES. Two dark boxes, and between them and the nose a viewer
            // can tell where somebody is looking from across a street — which
            // is the entire currency of a game about being noticed. Nothing
            // else on this body earns its two draw calls so cheaply.
            var eyeMat = Mat(new Color(0.10f, 0.09f, 0.09f));
            Box(Head, "EyeL", new Vector3(-0.042f, 0.055f, 0.083f),
                new Vector3(0.030f, 0.020f, 0.020f), eyeMat);
            Box(Head, "EyeR", new Vector3(0.042f, 0.055f, 0.083f),
                new Vector3(0.030f, 0.020f, 0.020f), eyeMat);

            // AND WHATEVER IS ON TOP. Bare, cropped, a full head of hair, or
            // a cap — one box whose height and depth come from the physique.
            // Two strangers matching from the neck down is ordinary; matching
            // from the neck up is what makes a crowd read as duplicated.
            double wear = Shape.Headwear;
            if (wear > 0.18)
            {
                var hairMat = Mat(HairColour(wear));
                float tall = 0.03f + 0.055f * (float)wear;
                Box(Head, "Hair", new Vector3(0, 0.145f - tall * 0.25f, -0.005f),
                    new Vector3(0.185f, tall, 0.195f), hairMat);
                // A peak, on the ones with the most on their head. It is a
                // cap, and it changes the silhouette more than the colour of
                // anything ever will.
                if (wear > 0.72)
                    Box(Head, "Peak", new Vector3(0, 0.135f - tall * 0.25f, 0.115f),
                        new Vector3(0.175f, 0.018f, 0.09f), hairMat);
            }

            foreach (var n in new[] { "Face", "EyeL", "EyeR", "Hair", "Peak" })
                MarkDetail(Head, n);

            (LThigh, LShin, LFoot) = Leg("L", -HipHalfWidth, clothMat, skinMat);
            (RThigh, RShin, RFoot) = Leg("R", HipHalfWidth, clothMat, skinMat);
            (LUpperArm, LForearm) = Arm("L", -ShoulderHalfWidth, clothMat, skinMat);
            (RUpperArm, RForearm) = Arm("R", ShoulderHalfWidth, clothMat, skinMat);
            MarkDetail(LForearm, "Hand");
            MarkDetail(RForearm, "Hand");
        }

        (Transform, Transform, Transform) Leg(string side, float x, Material cloth, Material skin)
        {
            var thigh = Joint(side + "Thigh", Hips, new Vector3(x, -HipToThigh, 0));
            Box(thigh, "ThighMesh", new Vector3(0, -ThighLength * 0.5f, 0),
                new Vector3(0.135f, ThighLength, 0.145f), cloth);

            var shin = Joint(side + "Shin", thigh, new Vector3(0, -ThighLength, 0));
            Box(shin, "ShinMesh", new Vector3(0, -ShinLength * 0.5f, 0),
                new Vector3(0.115f, ShinLength, 0.125f), cloth);

            var foot = Joint(side + "Foot", shin, new Vector3(0, -ShinLength, 0));
            // Offset FORWARD as well as down: a foot centred under the ankle
            // is a hoof, and it is the difference between a body that stands
            // and one that balances on stilts.
            Box(foot, "FootMesh", new Vector3(0, -(AnkleToSole - 0.035f), 0.055f),
                new Vector3(0.115f, 0.07f, 0.26f), skin);
            return (thigh, shin, foot);
        }

        (Transform, Transform) Arm(string side, float x, Material cloth, Material skin)
        {
            var upper = Joint(side + "UpperArm", Chest, new Vector3(x, NeckRise - 0.06f, 0));
            Box(upper, "UpperArmMesh", new Vector3(0, -UpperArmLength * 0.5f, 0),
                new Vector3(0.10f, UpperArmLength, 0.11f), cloth);

            var fore = Joint(side + "Forearm", upper, new Vector3(0, -UpperArmLength, 0));
            Box(fore, "ForearmMesh", new Vector3(0, -ForearmLength * 0.5f, 0),
                new Vector3(0.085f, ForearmLength, 0.095f), cloth);
            // A hand. Small, and doing the same job as the nose.
            Box(fore, "Hand", new Vector3(0, -ForearmLength - 0.05f, 0),
                new Vector3(0.075f, 0.11f, 0.055f), skin);
            return (upper, fore);
        }

        /// The small pieces — eyes, nose, hands, hair and whatever is on the
        /// head. Switched off at distance.
        ///
        /// NOT THE FEET, though this list said so for as long as it has
        /// existed. `MarkDetail` is called on the head's five pieces and on the
        /// two hands, and nowhere else; the feet have never been cullable. The
        /// same paragraph also sat stacked on `Joint`'s doc comment, so that
        /// function's description was attached to this field instead — the
        /// second time in one file.
        ///
        /// NOT THE LIMBS. The temptation with a body made of boxes is to cull
        /// from the outside in, and that is backwards: at fifty metres the
        /// arms and legs are what make a figure read as a person walking, and
        /// the nose is four pixels. Cut the pixels nobody can resolve and
        /// keep the ones doing the work.
        readonly System.Collections.Generic.List<GameObject> _detail
            = new System.Collections.Generic.List<GameObject>();
        bool _detailOn = true;

        public void SetDetail(bool on)
        {
            if (on == _detailOn) return;
            _detailOn = on;
            foreach (var go in _detail) if (go != null) go.SetActive(on);

            // AND THE SHADOW GOES TOO, past the same distance. A figure
            // thirty-five metres off is four pixels of shadow on a pavement
            // nobody is looking at, and it costs the same shadow-map draws as
            // the person standing next to the player. This is where most of
            // the saving is: it is forty walkers, not the two nearby.
            var mode = on ? UnityEngine.Rendering.ShadowCastingMode.On
                          : UnityEngine.Rendering.ShadowCastingMode.Off;
            if (_casters.Count == 0)
                foreach (var r in GetComponentsInChildren<MeshRenderer>(true))
                    if (r.shadowCastingMode == UnityEngine.Rendering.ShadowCastingMode.On)
                        _casters.Add(r);
            foreach (var r in _casters) if (r != null) r.shadowCastingMode = mode;
        }
        readonly System.Collections.Generic.List<MeshRenderer> _casters
            = new System.Collections.Generic.List<MeshRenderer>();

        void MarkDetail(Transform parent, string name)
        {
            var child = parent.Find(name);
            if (child != null) _detail.Add(child.gameObject);
        }

        /// Which pieces are part of the silhouette. Everything else is
        /// detail that lands inside a shadow something larger already cast.
        static bool Casts(string name) =>
            name == "Torso" || name == "Pelvis" || name == "Skull"
            || name == "ThighMesh" || name == "ShinMesh"
            || name == "UpperArmMesh" || name == "ForearmMesh"
            || name == "Hair";

        /// A bare transform at a joint position. The MESH is a child of it,
        /// offset half a limb down, so rotating the joint swings the limb from
        /// its end rather than about its middle. Parenting a scaled mesh
        /// directly and rotating THAT is the usual mistake and it makes every
        /// limb pivot around its own centre, which reads as a body coming
        /// apart.
        static Transform Joint(string name, Transform parent, Vector3 localPos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localRotation = Quaternion.identity;
            return go.transform;
        }

        static void Box(Transform parent, string name, Vector3 pos, Vector3 size, Material mat)
            => Piece(parent, name, pos, size, mat, Shared(PrimitiveType.Cube));

        static void Ball(Transform parent, string name, Vector3 pos, float d, Material mat)
            => Piece(parent, name, pos, new Vector3(d, d * 1.15f, d * 1.05f), mat,
                     Shared(PrimitiveType.Sphere));

        static void Piece(Transform parent, string name, Vector3 pos, Vector3 size,
                          Material mat, Mesh mesh)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = size;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = mat;
            // A BODY CASTS ONE SILHOUETTE, not thirteen.
            //
            // Every piece casting its own shadow is thirteen extra draws per
            // person into the shadow map, and the ones it buys are invisible:
            // a nose and two eyes cast onto a face that is already in shadow
            // from the skull in front of them. Only the masses cast — torso,
            // pelvis, head, and the four limb segments — which is the whole
            // readable silhouette for a bit over half the cost.
            //
            // Chosen after a CI sim run took eighty percent longer the day
            // bodies landed. On a runner with no GPU the shadow pass is the
            // dominant cost and thirteen small casters per walker is the
            // whole of it.
            r.shadowCastingMode = Casts(name)
                ? UnityEngine.Rendering.ShadowCastingMode.On
                : UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = true;
            r.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
            r.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.BlendProbes;
        }

        /// The primitive meshes, borrowed ONCE.
        ///
        /// `CreatePrimitive` per limb was the first version and it is the
        /// wrong shape twice over. It allocates a collider on every one of
        /// thirteen parts of every body — which then has to be destroyed, and
        /// `Destroy` is deferred to the end of the frame, so a spawning crowd
        /// spends a frame with several hundred stray colliders in it fighting
        /// the character controllers. And there is no reason for a hundred
        /// people to own a hundred copies of a cube.
        ///
        /// So: make one of each at startup, keep the mesh, throw the object
        /// away. Every body after that is transforms and renderers.
        static readonly System.Collections.Generic.Dictionary<PrimitiveType, Mesh> _meshes
            = new System.Collections.Generic.Dictionary<PrimitiveType, Mesh>();

        static Mesh Shared(PrimitiveType type)
        {
            if (_meshes.TryGetValue(type, out var m) && m != null) return m;
            var probe = GameObject.CreatePrimitive(type);
            m = probe.GetComponent<MeshFilter>().sharedMesh;
            Destroy(probe);
            _meshes[type] = m;
            return m;
        }

        /// Hair, from the same number that decided how much of it there is.
        /// Dark to fair across the range, because deriving it from a separate
        /// draw would just be another thing to keep uncorrelated for no gain.
        static Color HairColour(double wear)
        {
            float t = Mathf.Clamp01((float)((wear - 0.18) / 0.82));
            return Color.Lerp(new Color(0.10f, 0.08f, 0.07f),
                              new Color(0.55f, 0.45f, 0.30f), t);
        }

        static Material Mat(Color c)
        {
            var m = AssetLibrary.Opaque(c);
            return m;
        }
    }
}
