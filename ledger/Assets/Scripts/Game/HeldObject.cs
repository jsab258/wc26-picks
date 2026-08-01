using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// M17.8 — THE WEAPON IN THE HAND, which did not exist.
    ///
    /// The completeness audit on 2026-07-31 found nineteen weapons in `Arsenal`
    /// as data, with no mesh and nothing rendered anywhere. `weapons-spec.md`
    /// §5.1 says the THREAT is the main use of a weapon — brandishing is a verb
    /// of its own and Phase 3 wired it — and the object being threatened with
    /// was invisible. A game about being seen, in which the most legible thing
    /// a person can do is not drawn.
    ///
    /// PROCEDURAL, AND THAT IS THE RIGHT ANSWER RATHER THAN A COMPROMISE. The
    /// art direction (`production-plan-audio-art.md` §4A) chose stylised noir
    /// with **silhouette-first design so characters read at distance — which is
    /// exactly what the gaze and stance system needs.** At the range where a
    /// weapon changes what a witness reports, the thing being read is a
    /// SHAPE: long and thin, short and heavy, a bar, a loop of wire, nothing.
    /// A photoreal razor and a well-proportioned box are the same six pixels.
    ///
    /// So each family gets a silhouette built from the weapon's own numbers —
    /// `ReachMetres` is the length, `Concealment` is how much of it shows —
    /// rather than from a table of models this project does not have. When
    /// authored props arrive through `AssetLibrary`'s pack path, `TryInstantiateProp`
    /// takes over by name and nothing here changes.
    ///
    /// MESHES ARE SHARED, for the reason `Mannequin` learned: `CreatePrimitive`
    /// per object allocates a collider that then has to be destroyed, `Destroy`
    /// is deferred to end of frame, and a crowd drawing weapons would spend a
    /// frame with a few hundred stray colliders fighting the controllers.
    public static class HeldObject
    {
        static readonly Dictionary<PrimitiveType, Mesh> _meshes =
            new Dictionary<PrimitiveType, Mesh>();

        public static int Drawn { get; private set; }
        public static string LastDrawn { get; private set; }

        public static void ResetCounters() { Drawn = 0; LastDrawn = null; }

        static Mesh Shared(PrimitiveType type)
        {
            if (_meshes.TryGetValue(type, out var m) && m != null) return m;
            var probe = GameObject.CreatePrimitive(type);
            m = probe.GetComponent<MeshFilter>().sharedMesh;
            Object.Destroy(probe);
            _meshes[type] = m;
            return m;
        }

        /// Put this weapon in this hand. Returns the object so the caller can
        /// hide it again — except that `Arsenal.CanUndraw` is false, which is
        /// the one-way door the whole verb turns on, so in practice the only
        /// thing that removes it is the act ending.
        ///
        /// `hand` is `CharacterRig.HandAnchor` — the GRIP, already placed and
        /// already oriented for whichever body tier that person got, so the
        /// object goes on at local zero.
        ///
        /// IT USED TO BE THE FOREARM AND AN OFFSET, and that offset was a
        /// `Mannequin` constant, which quietly made this method mannequin-only.
        /// M17.1 gave the player a bought skeleton and the caller's
        /// `GetComponent&lt;Mannequin&gt;()` went null, so `hand` was null, so
        /// nothing was ever drawn and the threat gate failed on
        /// `drawn=0 object=none`. The offset now lives with the skeleton that
        /// knows its own proportions; this end holds no assumption about bodies
        /// at all.
        public static GameObject Draw(Transform hand, Weapon w)
        {
            if (hand == null || w == null) return null;

            // A PACK PROP WINS IF THERE IS ONE. The whole point of
            // `AssetLibrary`'s three tiers is that authored art replaces the
            // procedural version with no code change, and a held object is
            // exactly the kind of thing a prop bundle would carry.
            var prop = AssetLibrary.TryInstantiateProp("weapon_" + w.Id,
                                                       hand.position, hand.rotation);
            if (prop != null)
            {
                prop.transform.SetParent(hand, worldPositionStays: true);
                Drawn++;
                LastDrawn = w.Id;
                return prop;
            }

            var go = new GameObject("held_" + w.Id);
            go.transform.SetParent(hand, worldPositionStays: false);
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;

            Silhouette(go.transform, w);
            Drawn++;
            LastDrawn = w.Id;
            return go;
        }

        /// The shape, from the weapon's own numbers.
        ///
        /// `ReachMetres` is how far it lets you act from, which for a carried
        /// object is very nearly its length — a cosh reaches 1.0m and a razor
        /// 0.8m because that is arm plus object. Subtracting the arm leaves the
        /// object, and that is a derivation rather than a table of guesses.
        static void Silhouette(Transform parent, Weapon w)
        {
            // Arm's share of the reach. Upper arm plus forearm plus hand, from
            // `Mannequin`'s own constants so the two cannot drift.
            const float ArmShare = Mannequin.UpperArmLength + Mannequin.ForearmLength + 0.05f;
            float length = Mathf.Max(0.08f, (float)w.ReachMetres - ArmShare);

            // Darker than skin and darker than cloth, so it reads as a hard
            // object against a person in the restricted palette rather than as
            // another limb. The metal ones catch the sodium lamps, which is
            // most of what makes a drawn blade legible at night.
            bool metal = w.Family == Family.Edged || w.Family == Family.Firearm
                         || w.Family == Family.Blunt;
            // COLOUR CARRIES IT, NOT SMOOTHNESS. `AssetLibrary.Opaque` returns
            // a material CACHED BY COLOUR and shared across everything using
            // it, so setting smoothness on the instance would change every
            // other object of that colour in the scene — the same class of bug
            // as a second copy of a threshold, in the other direction. Metal
            // reads lighter and cooler instead, which at the distance this
            // silhouette is meant to be legible at is the part that carries.
            var colour = metal ? new Color(0.34f, 0.36f, 0.40f)
                               : new Color(0.16f, 0.14f, 0.13f);

            switch (w.Family)
            {
                case Family.Edged:
                    // Thin and long, held point-down: the most recognisable
                    // silhouette in the set and the one the street reacts to.
                    Part(parent, "blade", new Vector3(0, -length * 0.5f, 0),
                         new Vector3(0.012f, length, 0.045f), colour);
                    Part(parent, "grip", new Vector3(0, 0.02f, 0),
                         new Vector3(0.030f, 0.09f, 0.035f),
                         new Color(0.12f, 0.10f, 0.09f));
                    break;

                case Family.Blunt:
                    Part(parent, "shaft", new Vector3(0, -length * 0.5f, 0),
                         new Vector3(0.042f, length, 0.042f), colour);
                    // Weight at the far end, which is what a cosh IS.
                    Part(parent, "head", new Vector3(0, -length, 0),
                         new Vector3(0.062f, 0.075f, 0.062f), colour);
                    break;

                case Family.Ligature:
                    // A loop, not a line: two hands' worth of cord between the
                    // fists. Read as a shape rather than modelled as a curve.
                    Part(parent, "loop", new Vector3(0, -0.10f, 0),
                         new Vector3(0.18f, 0.010f, 0.010f), colour);
                    Part(parent, "tail", new Vector3(0, -0.05f, 0),
                         new Vector3(0.010f, 0.11f, 0.010f), colour);
                    break;

                case Family.Firearm:
                    Part(parent, "frame", new Vector3(0, -0.03f, -0.06f),
                         new Vector3(0.030f, 0.070f, 0.170f), colour);
                    Part(parent, "grip", new Vector3(0, -0.09f, 0.01f),
                         new Vector3(0.032f, 0.090f, 0.050f),
                         new Color(0.11f, 0.09f, 0.08f));
                    break;

                case Family.Kit:
                    Part(parent, "case", new Vector3(0, -0.09f, 0),
                         new Vector3(0.11f, 0.15f, 0.05f), colour);
                    break;

                // Hands hold nothing, and an environment kill has no object at
                // all — which is most of why it reads as an accident. Drawing
                // something here would be the bug.
                case Family.Hands:
                case Family.Environment:
                default:
                    break;
            }
        }

        static void Part(Transform parent, string name, Vector3 at, Vector3 size,
                         Color colour)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, worldPositionStays: false);
            go.transform.localPosition = at;
            go.transform.localScale = size;
            go.AddComponent<MeshFilter>().sharedMesh = Shared(PrimitiveType.Cube);
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = AssetLibrary.Opaque(colour);
            // NO SHADOW FROM A THING THIS SMALL. It costs a shadow-map pass per
            // drawn weapon across a crowd and contributes a few pixels; the
            // silhouette that matters is the one against the street, and that
            // comes from the body.
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = true;
            r.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
        }

        /// Whether this weapon shows at all when carried rather than drawn.
        /// `Concealment.Impossible` is a bat or a sawn-off — carried visibly,
        /// which the spec says is a different decision entirely, and the street
        /// should be able to see that decision.
        public static bool VisibleWhenCarried(Weapon w) =>
            w != null && w.Concealment == Concealment.Impossible;
    }
}
