using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// Gulls over the docks (town-plan.md T4).
    ///
    /// Twelve birds on slow deterministic circles above Ironside and the
    /// quay line, each three white boxes — body and two wings — with the
    /// wings flapping on a sine and the circle bobbing gently. One Update
    /// drives all of them; there is no physics, no avoidance, no state.
    /// A gull's entire job is to be a distant moving fleck that says PORT,
    /// and at the distances these fly nobody can tell a box from a bird —
    /// the same argument the cable's two segments won.
    ///
    /// Deterministic: every path parameter comes from the gull's index, so
    /// the same sky happens in every run and the CI stills stay comparable
    /// (frame-for-frame they differ with time of capture, but the FLOCK,
    /// its centres and its radii do not).
    public class GullHost : MonoBehaviour
    {
        readonly List<Transform> _gulls = new List<Transform>();
        readonly List<Transform> _wingsL = new List<Transform>();
        readonly List<Transform> _wingsR = new List<Transform>();

        /// Circle centres: over the Ironside yards and off the quay line
        /// south of them, where the map implies water.
        static readonly Vector3[] Centres =
        {
            new Vector3(-20f, 26f, -140f),
            new Vector3(25f, 32f, -160f),
            new Vector3(0f, 22f, -175f),
            new Vector3(60f, 28f, -150f),
        };

        public int Build()
        {
            for (int i = 0; i < 12; i++)
            {
                var body = GameObject.CreatePrimitive(PrimitiveType.Cube);
                body.name = $"Gull_{i}";
                body.transform.SetParent(transform, false);
                body.transform.localScale = new Vector3(0.16f, 0.10f, 0.45f);
                Object.Destroy(body.GetComponent<Collider>());
                var rend = body.GetComponent<Renderer>();
                rend.sharedMaterial = AssetLibrary.Material(AssetLibrary.Plaster);
                var mpb = new MaterialPropertyBlock();
                mpb.SetColor("_Color", new Color(0.92f, 0.92f, 0.94f));
                rend.SetPropertyBlock(mpb);

                Transform Wing(string n, float side)
                {
                    var w = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    w.name = n;
                    w.transform.SetParent(body.transform, false);
                    w.transform.localPosition = new Vector3(side * 2.6f, 0f, 0f);
                    w.transform.localScale = new Vector3(5f, 0.25f, 0.55f);
                    Object.Destroy(w.GetComponent<Collider>());
                    var wr = w.GetComponent<Renderer>();
                    wr.sharedMaterial = AssetLibrary.Material(AssetLibrary.Plaster);
                    wr.SetPropertyBlock(mpb);
                    return w.transform;
                }
                _wingsL.Add(Wing($"Gull_{i}_wl", -1f));
                _wingsR.Add(Wing($"Gull_{i}_wr", 1f));
                _gulls.Add(body.transform);
            }
            return _gulls.Count;
        }

        void Update()
        {
            float t = Time.time;
            for (int i = 0; i < _gulls.Count; i++)
            {
                var c = Centres[i % Centres.Length];
                float radius = 14f + (i * 7) % 22;
                float speed = 0.10f + 0.035f * (i % 4);           // rad/s, slow
                float phase = i * 2.09f;
                float a = t * speed + phase;
                var pos = c + new Vector3(Mathf.Cos(a) * radius,
                                          Mathf.Sin(t * 0.5f + phase) * 1.6f,
                                          Mathf.Sin(a) * radius);
                var fwd = new Vector3(-Mathf.Sin(a), 0f, Mathf.Cos(a));   // tangent
                _gulls[i].SetPositionAndRotation(pos, Quaternion.LookRotation(fwd));

                // Glide mostly, flap in bursts: gulls beat and then hold,
                // and the hold is what reads as a seabird from below.
                float beat = Mathf.Sin(t * 5f + phase);
                float flap = Mathf.Max(0f, Mathf.Sin(t * 0.7f + phase * 1.7f)) * 24f;
                _wingsL[i].localRotation = Quaternion.Euler(0, 0, beat * flap + 4f);
                _wingsR[i].localRotation = Quaternion.Euler(0, 0, -beat * flap - 4f);
            }
        }
    }
}
