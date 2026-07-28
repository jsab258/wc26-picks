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
    /// It is also not throwaway. The bones are the contract: when the FBX
    /// lands, `CharacterRig` binds to an Avatar instead of to this, drives the
    /// identical joints with the identical numbers, and this class stops being
    /// instantiated. Nothing downstream of it changes.
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

        /// Build a body onto `host`, replacing whatever primitive mesh it was
        /// wearing. The host keeps its collider, its controller and its
        /// scripts — only the visible shape changes.
        /// This body's proportions. Public so the rig can read the gait bias
        /// and so the sim gate can prove a crowd is not thirty of one person.
        public Physique Shape { get; private set; }

        public static Mannequin Build(GameObject host, Color skin, Color cloth, string who = null)
        {
            if (host == null) return null;
            var existing = host.GetComponent<Mannequin>();
            if (existing != null) return existing;

            // The capsule mesh goes. Its renderer, not the object — anything
            // holding a reference to the transform still has one.
            var own = host.GetComponent<MeshRenderer>();
            if (own != null) Destroy(own);
            var ownMesh = host.GetComponent<MeshFilter>();
            if (ownMesh != null) Destroy(ownMesh);

            var m = host.AddComponent<Mannequin>();
            m.Shape = Physique.For(string.IsNullOrEmpty(who) ? host.name : who);
            m.Assemble(skin, cloth);
            return m;
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

            (LThigh, LShin, LFoot) = Leg("L", -HipHalfWidth, clothMat, skinMat);
            (RThigh, RShin, RFoot) = Leg("R", HipHalfWidth, clothMat, skinMat);
            (LUpperArm, LForearm) = Arm("L", -ShoulderHalfWidth, clothMat, skinMat);
            (RUpperArm, RForearm) = Arm("R", ShoulderHalfWidth, clothMat, skinMat);
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
            go.AddComponent<MeshRenderer>().sharedMaterial = mat;
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

        static Material Mat(Color c)
        {
            var m = AssetLibrary.Opaque(c);
            return m;
        }
    }
}
