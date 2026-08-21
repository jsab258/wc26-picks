using UnityEngine;

namespace Ledger.Game
{
    /// A soft dark ellipse under every body — see LedgerBlob.shader for why
    /// this exists and why it multiplies. One shared mesh, one shared
    /// material, one shared texture: the whole crowd's blobs are candidates
    /// for dynamic batching, and nothing here allocates per frame.
    public static class BlobShadow
    {
        /// How many are live — the denominator for a still that shows bodies
        /// floating. Zero with walkers on screen means Attach was never
        /// called or the shader failed to load, and `Why` says which.
        public static int Count;
        public static string Why = "not tried";

        static Material _mat;
        static Mesh _quad;
        static Texture2D _falloff;

        /// Fade with the night — the blob proxies the SUN's contact shadow,
        /// and under lamps it should be a hint, not a stamp. Called from
        /// GameController's light drive off the same NightAmount the sun and
        /// the grade already use, so dusk cannot arrive at two brightnesses.
        public static void Tick(float night)
        {
            if (_mat != null)
                _mat.SetFloat("_Strength", Mathf.Lerp(0.42f, 0.16f, night));
        }

        public static void Attach(GameObject host, float groundLocalY)
        {
            if (host == null) return;
            if (host.transform.Find("BlobShadow") != null) return;
            if (!Ensure()) return;

            var go = new GameObject("BlobShadow");
            go.transform.SetParent(host.transform, false);
            // A hair above the ground plane; polygon offset in the shader
            // does the rest of the z-fight avoidance.
            go.transform.localPosition = new Vector3(0, groundLocalY + 0.015f, 0);
            go.transform.localRotation = Quaternion.Euler(90f, 0, 0);
            // Wider than deep: a standing figure's footprint, not a coin.
            go.transform.localScale = new Vector3(0.85f, 0.55f, 1f);
            var mf = go.AddComponent<MeshFilter>();
            mf.sharedMesh = _quad;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = _mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            Count++;
        }

        static bool Ensure()
        {
            if (_mat != null) return true;
            var sh = Shader.Find("Hidden/LedgerBlob");
            if (sh == null) { Why = "shader missing"; return false; }

            // Radial falloff, smooth to zero at the rim so the multiply
            // reaches identity exactly at the edge — a hard rim is a decal,
            // a soft one is a shadow.
            const int N = 64;
            _falloff = new Texture2D(N, N, TextureFormat.Alpha8, false)
            { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var px = new Color32[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float dx = (x + 0.5f) / N - 0.5f, dy = (y + 0.5f) / N - 0.5f;
                    float r = Mathf.Sqrt(dx * dx + dy * dy) * 2f;
                    float a = Mathf.Clamp01(1f - r);
                    a = a * a * (3f - 2f * a);          // smoothstep profile
                    px[y * N + x] = new Color32(255, 255, 255, (byte)(a * 255));
                }
            _falloff.SetPixels32(px);
            _falloff.Apply(false, true);

            _mat = new Material(sh);
            _mat.SetTexture("_MainTex", _falloff);
            _mat.SetFloat("_Strength", 0.42f);

            _quad = new Mesh { name = "BlobQuad" };
            _quad.vertices = new[]
            {
                new Vector3(-0.5f, -0.5f, 0), new Vector3(0.5f, -0.5f, 0),
                new Vector3(-0.5f,  0.5f, 0), new Vector3(0.5f,  0.5f, 0),
            };
            _quad.uv = new[]
            {
                new Vector2(0, 0), new Vector2(1, 0),
                new Vector2(0, 1), new Vector2(1, 1),
            };
            _quad.triangles = new[] { 0, 2, 1, 1, 2, 3 };
            _quad.RecalculateBounds();
            Why = "ok";
            return true;
        }
    }
}
