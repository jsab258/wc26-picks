using UnityEditor;
using UnityEngine;

namespace Ledger.EditorTools
{
    /// THE SKY CAPTURES IMPORT AS CUBEMAPS, AS CODE, BECAUSE THERE ARE NO
    /// `.meta` FILES (the CharacterImport convention, applied to textures).
    ///
    /// Unity's default for an `.hdr` is a plain 2D texture. The reflection
    /// slot (`RenderSettings.customReflectionTexture`) accepts only a cube,
    /// so on 24 Aug every bind threw `ArgumentException: 2D given while only
    /// CUBE is supported` — once per frame, 593,328 log lines in one run,
    /// and the sim was killed at its 24-minute cap having reached one shot.
    /// The runtime side now refuses to bind a non-cube at all (fail-closed,
    /// `SkyEnvironment.Take`), so a missing or broken import costs a verdict
    /// key, never a stalled build — this file is what makes the captures
    /// actually WORK.
    ///
    /// Scoped by path, not by extension: other HDR textures may arrive some
    /// day with their own correct shapes, and an importer that rewrites
    /// every `.hdr` in the project is the allow-list fault inverted.
    public class SkyImport : AssetPostprocessor
    {
        const string SkyPath = "Assets/Resources/Sky/polyhaven/";

        void OnPreprocessTexture()
        {
            if (!assetPath.Replace('\\', '/').StartsWith(SkyPath)) return;
            var imp = (TextureImporter)assetImporter;
            imp.textureShape = TextureImporterShape.TextureCube;
            // The captures are equirectangular panoramas; Auto detects the
            // layout from the aspect and wraps them onto the cube.
            imp.generateCubemap = TextureImporterGenerateCubemap.AutoCubemap;
            // No convolution: these feed GLOSSY reflections through the
            // standard shader's own mip selection. Specular convolution here
            // would pre-blur the top mip that smoothness 0.90 glass reads.
            imp.cubemapConvolution = TextureImporterCubemapConvolution.None;
            // 512 per face. The reflection was a 64px gradient before, so
            // this is an 8x step up in the direction that matters while
            // keeping four cubemaps' GPU cost modest; raise it off a still
            // that says the reflections read soft, not by default.
            imp.maxTextureSize = 512;
            imp.mipmapEnabled = true;
            Debug.Log($"SkyImport: {assetPath} -> cube 512 (auto-from-equirect)");
        }
    }
}
