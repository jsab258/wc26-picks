using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Grain, vignette and bloom — the last three items of the art direction
    /// (production-plan-audio-art.md §4: "Post: film grain, vignette, slight
    /// bloom on light sources").
    ///
    /// Built by hand rather than with the Post Processing package, for the
    /// same reason every other asset here is synthesised: no extra package,
    /// no version pinning, no import step, works in the built player today.
    /// A full-screen blit with one shader is what those three effects
    /// actually are.
    ///
    /// WHAT EACH ONE IS FOR, because "add post" is not a reason:
    ///
    ///   - **Vignette** darkens the corners, which pulls the eye to the
    ///     middle and makes a frame feel photographed rather than rendered.
    ///     It is also the cheapest way to make a wide FOV feel intimate,
    ///     which this game needs — it is about people at conversational
    ///     distance, not landscapes.
    ///   - **Grain** is the one that does the most work for the least money.
    ///     It hides banding in the dark blue-teal night sky, it hides the
    ///     flatness of untextured geometry, and it unifies everything under
    ///     one film stock — which is exactly the trick a low-budget project
    ///     needs, because it makes disparate assets look like they were
    ///     photographed together.
    ///   - **Bloom** on the neon is the whole reason the neon exists. A
    ///     bright pixel that does not spill light is a coloured rectangle;
    ///     one that does is a LAMP. It also recovers the colour that LDR
    ///     clipping takes away, by spreading hue into the pixels around a
    ///     highlight rather than only inside it.
    ///
    /// Grain gets stronger at night and in rain, because that is when a real
    /// film stock is being pushed and when we most need to hide flatness.
    public class FilmGrade : MonoBehaviour
    {
        static FilmGrade _instance;

        /// Frames on which occlusion was actually computed. The sim gate
        /// reads this: an effect that silently stops running looks exactly
        /// like one that is running and doing nothing.
        public static int Applied { get; private set; }

        Material _mat, _ao;
        RenderTexture _bloomA, _bloomB;
        Camera _cam;

        public static void Ensure(Camera cam)
        {
            if (_instance != null || cam == null) return;
            var go = new GameObject("FilmGrade");
            go.transform.SetParent(cam.transform, false);
            _instance = go.AddComponent<FilmGrade>();
            _instance._cam = cam;
            // HDR, or the tonemap has nothing to map: without it the frame
            // buffer clips at 1.0 BEFORE the curve ever sees it, and the
            // roll-off is applied to a value that has already lost its hue.
            cam.allowHDR = true;
            _instance.Build();
        }

        void Build()
        {
            var shader = Shader.Find("Hidden/LedgerFilmGrade");
            if (shader == null || !shader.isSupported)
            {
                // No shader, no grade. Never a black screen: an art effect
                // that can fail closed must, because the alternative is a
                // player who cannot see the game.
                enabled = false;
                return;
            }
            _mat = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };

            // AMBIENT OCCLUSION, in its OWN material off its own shader.
            //
            // `Shader.isSupported` is per-shader, not per-pass, so while the
            // AO passes lived in the grade shader a compile error in either
            // of them would have disabled grain, vignette, bloom and the
            // tonemap along with them. This class's own header says an art
            // effect that can break the picture must never be able to — and
            // a newer, riskier effect sharing its compilation unit is
            // exactly that risk, one level down.
            //
            // Now AO can fail entirely and the frame is merely un-occluded.
            var aoShader = Shader.Find("Hidden/LedgerAo");
            if (aoShader != null && aoShader.isSupported)
                _ao = new Material(aoShader) { hideFlags = HideFlags.HideAndDontSave };

            // Depth AND normals, and this one line is what makes
            // `_CameraDepthNormalsTexture` exist at all. Without it the AO
            // pass samples a texture Unity never rendered and returns a
            // uniform grey — which looks like a shader bug and is a missing
            // request.
            if (_cam != null) _cam.depthTextureMode |= DepthTextureMode.DepthNormals;
        }

        /// Whether occlusion is worth its passes at all. Off is a real
        /// setting: this is three extra full-screen operations, and on a
        /// machine that is already missing frame time the honest trade is to
        /// drop the effect rather than the frame rate.
        public static bool AmbientOcclusion = true;

        void OnRenderImage(RenderTexture src, RenderTexture dst)
        {
            if (_mat == null) { Graphics.Blit(src, dst); return; }

            var s = GameSettings.Current;
            // NIGHT AND RAIN PUSH THE STOCK. More grain when there is less
            // light, which is both true of film and exactly when we need it
            // to hide banding in a dark sky.
            float night = GameController.NightAmount;
            float grain = (0.020f + 0.045f * night + 0.020f * Weather.Rain) * s.GrainAmount;
            float vignette = 0.34f + 0.16f * night;

            // BLOOM: downsample, blur, add back. Two small textures rather
            // than a chain — at this scale the extra passes buy nothing you
            // can see, and every one costs a frame budget we have already
            // measured as tight.
            int w = Mathf.Max(2, src.width / 4), h = Mathf.Max(2, src.height / 4);
            _bloomA = RenderTexture.GetTemporary(w, h, 0, src.format);
            _bloomB = RenderTexture.GetTemporary(w, h, 0, src.format);
            _mat.SetFloat("_Threshold", 0.62f);
            Graphics.Blit(src, _bloomA, _mat, 1);            // pass 1: bright pass
            _mat.SetVector("_Dir", new Vector4(1f / w, 0, 0, 0));
            Graphics.Blit(_bloomA, _bloomB, _mat, 2);        // pass 2: blur X
            _mat.SetVector("_Dir", new Vector4(0, 1f / h, 0, 0));
            Graphics.Blit(_bloomB, _bloomA, _mat, 2);        // pass 2: blur Y

            _mat.SetTexture("_BloomTex", _bloomA);
            _mat.SetFloat("_Bloom", 0.55f + 0.35f * night);
            _mat.SetFloat("_Grain", grain);
            _mat.SetFloat("_Vignette", vignette);
            // The aperture opens at night and closes in daylight rain, from
            // the same curve the scene lighting uses.
            _mat.SetFloat("_Exposure", (float)Ledger.Core.LightModel.Exposure(night, Weather.Rain));
            // A grain that does not move is dirt on the lens. Seeded per
            // frame off unscaled time so it keeps crawling even when the
            // game is paused behind a panel.
            _mat.SetFloat("_Seed", Time.unscaledTime * 37.13f % 1000f);

            // OCCLUSION, at half resolution and blurred twice.
            //
            // Half res is not a compromise here, it is the right resolution:
            // contact darkening is low-frequency by nature and the blur that
            // has to follow a twelve-tap kernel would throw away the extra
            // detail anyway. Full res would cost four times as much to
            // produce an image the next pass erases.
            RenderTexture aoA = null, aoB = null;
            if (AmbientOcclusion && _cam != null && _ao != null)
            {
                int aw = Mathf.Max(2, src.width / 2), ah = Mathf.Max(2, src.height / 2);
                aoA = RenderTexture.GetTemporary(aw, ah, 0, RenderTextureFormat.R8);
                aoB = RenderTexture.GetTemporary(aw, ah, 0, RenderTextureFormat.R8);
                _ao.SetFloat("_AoRadius", (float)LightModel.AoRadiusMetres);
                _ao.SetVector("_AoTexelSize", new Vector4(1f / aw, 1f / ah, aw, ah));
                // The projection matrix, so the AO pass can turn a UV back
                // into a view-space ray. Taken from the camera rather than
                // assumed, because a changed FOV would otherwise silently
                // scale the sampling radius.
                _ao.SetMatrix("_AoProj", _cam.projectionMatrix);
                Graphics.Blit(src, aoA, _ao, 0);             // occlusion
                _ao.SetVector("_Dir", new Vector4(1f / aw, 0, 0, 0));
                Graphics.Blit(aoA, aoB, _ao, 1);             // blur X, edge-aware
                _ao.SetVector("_Dir", new Vector4(0, 1f / ah, 0, 0));
                Graphics.Blit(aoB, aoA, _ao, 1);             // blur Y
                _mat.SetTexture("_AoTex", aoA);
                _mat.SetFloat("_AoStrength",
                    (float)LightModel.AoStrength(night, Weather.Rain));
                _mat.SetFloat("_AoRelief", 0.65f);
                _mat.SetFloat("_AoFloor", 0.35f);
                Applied++;
            }
            else
            {
                // Fails to NO occlusion rather than to full occlusion. A
                // missing AO texture reads as black, and black in this term
                // means fully enclosed — so the failure mode of forgetting
                // this branch is a completely dark frame.
                _mat.SetTexture("_AoTex", Texture2D.blackTexture);
                _mat.SetFloat("_AoStrength", 0f);
                _mat.SetFloat("_AoRelief", 0f);
                _mat.SetFloat("_AoFloor", 1f);
            }

            Graphics.Blit(src, dst, _mat, 0);

            if (aoA != null) RenderTexture.ReleaseTemporary(aoA);
            if (aoB != null) RenderTexture.ReleaseTemporary(aoB);
            RenderTexture.ReleaseTemporary(_bloomA);
            RenderTexture.ReleaseTemporary(_bloomB);
        }
    }
}
