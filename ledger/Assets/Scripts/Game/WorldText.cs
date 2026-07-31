using System.Collections.Generic;
using UnityEngine;

namespace Ledger.Game
{
    /// Every `TextMesh` in the world, wearing a shader that respects depth.
    ///
    /// WHY THIS EXISTS is written at the top of `Resources/LedgerText.shader`
    /// and was found by looking at the first screenshot this project could
    /// commit: names floating over the skyline, street signs reading as garbled
    /// overlapping glyphs. Unity's built-in text shader is `ZTest Always`.
    ///
    /// THE ATLAS MOVES, AND THAT IS THE TRAP. A dynamic font rebuilds its
    /// texture whenever a glyph it has not rasterised yet is asked for — and
    /// the rebuild can hand back a DIFFERENT texture object. A material that
    /// captured the old one at startup then samples a dead atlas and every
    /// label in the game renders blank. That failure would look exactly like
    /// success from the C# side: the TextMesh still has its text, still
    /// reports a sensible `preferredWidth`, and draws nothing.
    ///
    /// So the texture is re-bound on `Font.textureRebuilt`, and the sim counts
    /// how many labels ended up on this material rather than assuming the
    /// assignment took — `Adopted` is read by a gate, because a helper nothing
    /// calls and a helper that silently does nothing look identical from here.
    public static class WorldText
    {
        /// How many TextMesh renderers this has re-materialised, and how many
        /// it could not. Read by the sim verdict.
        public static int Adopted { get; private set; }
        public static int Refused { get; private set; }

        /// Null when the shader is not in the build. That is a real
        /// possibility and it is why the ring shader exists at all, so it is
        /// reported rather than assumed away.
        public static bool ShaderPresent => _shader != null;

        static Shader _shader;
        static bool _looked;
        static readonly Dictionary<Font, Material> _byFont = new Dictionary<Font, Material>();
        static bool _hooked;

        /// Put a depth-testing material on this label. Safe to call twice.
        ///
        /// Returns false and leaves the built-in material alone if the shader
        /// is missing — a mirrored sign is a bad look, and an invisible one is
        /// a worse one, so this never trades the second fault for the first.
        public static bool Adopt(TextMesh tm)
        {
            if (tm == null) return false;
            var r = tm.GetComponent<MeshRenderer>();
            if (r == null || tm.font == null) { Refused++; return false; }

            if (!_looked) { _shader = Shader.Find("Hidden/LedgerText"); _looked = true; }
            if (_shader == null) { Refused++; return false; }

            if (!_hooked)
            {
                Font.textureRebuilt += OnAtlasRebuilt;
                _hooked = true;
            }

            r.sharedMaterial = MaterialFor(tm.font);
            Adopted++;
            return true;
        }

        /// ONE MATERIAL PER FONT, not per label. The street has forty-odd
        /// signs and every walker carries a name; a material each would be a
        /// material each, and TextMesh renderers already do not batch.
        static Material MaterialFor(Font font)
        {
            if (_byFont.TryGetValue(font, out var m) && m != null) return m;
            m = new Material(_shader) { name = "mat_worldtext_" + font.name };
            m.mainTexture = font.material != null ? font.material.mainTexture : null;
            _byFont[font] = m;
            return m;
        }

        /// The atlas was rebuilt, so every material pointing at the old one is
        /// now pointing at nothing. Re-bind rather than rebuild: the material
        /// is fine, only its texture moved.
        static void OnAtlasRebuilt(Font font)
        {
            if (font == null) return;
            if (_byFont.TryGetValue(font, out var m) && m != null && font.material != null)
                m.mainTexture = font.material.mainTexture;
        }

        /// For the sim, which runs several worlds in one process.
        public static void ResetCounters()
        {
            Adopted = 0;
            Refused = 0;
        }
    }
}
