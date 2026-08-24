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

        /// Frames on which the grade ran AT ALL.
        ///
        /// Separate from `Applied`, and added the night the AO gate revealed
        /// that `OnRenderImage` had never once been called: attached to a
        /// child of the camera instead of the camera, this whole class was a
        /// component sitting in a scene doing nothing, and every check passed
        /// because every check was of the model rather than of the picture.
        /// One counter makes that failure impossible to have again.
        public static int Frames { get; private set; }

        Material _mat, _ao;
        RenderTexture _bloomA, _bloomB;
        Camera _cam;

        /// ON THE CAMERA'S OWN GAMEOBJECT. Not a child of it.
        ///
        /// `OnRenderImage` is only delivered to components attached to the
        /// GameObject that HAS the Camera. This class used to be added to a
        /// child transform parented under the camera — which looks tidy,
        /// keeps the hierarchy clean, and means the entire post stack never
        /// executed a single frame. Grain, vignette, bloom, the exposure and
        /// the ACES tonemap have all been dead since they were written.
        ///
        /// Nothing caught it because nothing ever asserted that post reached
        /// PIXELS. Every check was of the model — the curves are tested in
        /// `Core/LightModel`, the shader compiled, the material built, the
        /// component existed. The first check that rendered one frame with an
        /// effect and one without found it immediately, and it was written
        /// for ambient occlusion, four features later.
        public static void Ensure(Camera cam)
        {
            if (_instance != null || cam == null) return;
            _instance = cam.gameObject.AddComponent<FilmGrade>();
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

            // Depth AND normals via ApplyPreset — see it for why the request
            // is conditional now.
            ApplyPreset();
        }

        /// The preset's half of the stack, applied where the other quality
        /// levers are applied (SceneLighting.ApplyQuality calls this).
        ///
        /// The DepthNormals request is the reason this exists: it is not a
        /// texture flag, it is A WHOLE EXTRA RENDER OF THE SCENE every
        /// frame, and it was requested unconditionally even though its only
        /// consumer is the AO pass. On Low and Medium the AO never runs, so
        /// the prepass was a full scene render feeding a texture nothing
        /// sampled. Cleared, not just left unused — and re-requested the
        /// moment the slider returns to High, no restart.
        public static void ApplyPreset()
        {
            if (_instance == null || _instance._cam == null) return;
            bool occlusion = Ledger.Core.Detail.PostOcclusion(
                Ledger.Core.Detail.Parse(GameSettings.Current.Detail));
            if (occlusion)
                _instance._cam.depthTextureMode |= DepthTextureMode.DepthNormals;
            else
                _instance._cam.depthTextureMode &= ~DepthTextureMode.DepthNormals;
        }

        /// Whether occlusion is worth its passes at all. Off is a real
        /// setting: this is three extra full-screen operations, and on a
        /// machine that is already missing frame time the honest trade is to
        /// drop the effect rather than the frame rate.
        public static bool AmbientOcclusion = true;

        /// PER-EFFECT SWITCHES, for the A/B gates.
        ///
        /// Not options and not quality settings — these exist so the sim can
        /// render one frame with an effect and one without and compare. That
        /// is the only check that has ever caught a post effect not reaching
        /// pixels, and it caught the whole stack being dead the first time it
        /// ran. Every effect here now has one.
        public static bool Grain = true, Vignette = true, Bloom = true;
        /// The night black-lift's A/B switch, same contract as the three
        /// above: not an option, exists so the night-floor probe can render
        /// one frame without the lift and say what the lift costs.
        public static bool Lift = true;

        /// How lit the player currently is, 0..1 — set by the game each frame
        /// from the same `Perceivers.LevelAt` the NPCs read.
        ///
        /// ONE SOURCE, TWO CONSUMERS, and that is deliberate: the symmetry
        /// rule promises the player that what they can read off the frame and
        /// what the city can see are the same fact. Two independently
        /// maintained numbers would make the promise a lie the first time they
        /// drifted, and this project has already watched a threshold drift
        /// apart from its own copy once.
        public static float LitAmount = 1f;

        /// What actually reached the shader, for the verdict. Both stuck at
        /// exactly 1.0000 means either `LitAmount` never moves or this code
        /// never runs, and from outside those are the same reading — which is
        /// how the model they come from spent weeks written and unwired.
        public static double LastTempR = 1.0, LastTempB = 1.0;

        /// THE GRAIN AMPLITUDE THAT ACTUALLY REACHED THE SHADER, for the
        /// verdict — added 24 Aug because the amount this chain applies had
        /// never once been printed, and the first instrument pointed at it
        /// (`tools/ref-bench.py`) read our stills at three to seven times the
        /// noisiest GTA reference frame. A number the render is built on that
        /// nobody outside this file can see is a number nobody can calibrate.
        ///
        /// `LastGrain` is LAST-WINS: the value `_Grain` was set from on the
        /// most recently graded frame. `GrainLo`/`GrainHi` are the run's
        /// minimum and maximum of it, and they are needed because ONE
        /// expression below drives day, night and rain — a single sample
        /// cannot show that span, and the span is the whole question.
        ///
        /// The AUTHORED amount, read BEFORE the `Grain` A/B switch: the sim
        /// renders half its measurement frames with grain forced off, and a
        /// field recording what was PUSHED would read 0.000 on exactly those
        /// frames — which is also what "the grade never ran" looks like.
        ///
        /// -1 until the grade has run once, so "nothing measured" cannot be
        /// mistaken for "no grain" (rule 3b: a zero needs a denominator, and
        /// here the denominator is whether the pass executed at all).
        public static double LastGrain = -1, GrainLo = -1, GrainHi = -1;

        /// Pass the frame straight through — no tonemap, no exposure, no
        /// anything. For the sim's light-attribution probe: "is the night
        /// frame bright before the grade touches it, or because of it?" is
        /// the first question to ask and there was no way to ask it.
        public static bool Bypass = false;

        /// A/B multiplier on the aperture, for the sim's exposure response
        /// ladder ONLY — never a setting and never written by the game.
        ///
        /// `Exposure`'s own history is six revisions of somebody choosing a
        /// number, landing a build, and reading one frame: the comments on
        /// it record 0.55 -> 0.10 -> below zero on the night arm alone, and
        /// a day arm moved three times because "the tonemap rolls off, so
        /// the arm buys less than linear". Nobody has ever printed the
        /// CURVE. day3_noon at meanLuma 0.206 against day3_night 0.165 is
        /// the cost: our midday is a quarter brighter than our midnight,
        /// and a real overcast noon frame sits near 0.35-0.50.
        ///
        /// So the sim renders the same noon instant at several apertures
        /// and reports what each produced. Then the number comes off the
        /// series instead of off an argument.
        public static float ExposureScale = 1f;

        void OnRenderImage(RenderTexture src, RenderTexture dst)
        {
            Frames++;
            if (Bypass || _mat == null) { Graphics.Blit(src, dst); return; }

            var s = GameSettings.Current;
            // NIGHT AND RAIN PUSH THE STOCK. More grain when there is less
            // light, which is both true of film and exactly when we need it
            // to hide banding in a dark sky.
            float night = GameController.NightAmount;
            // CALIBRATED AGAINST THE GTA REFERENCE FRAMES — EVERY TERM /4
            // (24 Aug). The night term's own ladder before that was
            // 0.045 → 0.028 → 0.022 for LINEAR (V1.5, two rounds), each step
            // taken off one night frame by eye; the day and rain terms had
            // never been moved at all. This is the first time any of the
            // three has been set against a measurement of somebody else's
            // film stock rather than against our own last frame.
            //
            // WHERE THE FOUR COMES FROM. `tools/ref-bench.py --series` on
            // this checkout's stills, Immerkaer noise sigma over the ground
            // band in 0..255 levels:
            //
            //   the five GTA refs   0.23 · 0.85 · 0.89 · 1.71 · 2.05
            //   the seven districts 5.21 · 5.54 · 5.65 · 5.66 · 5.99
            //                       · 6.43 · 7.51
            //
            // The districts are the calibration target and not the review
            // stills, for two reasons that are both about them being a
            // SERIES: they are the pose-stable frames (one fixed camera per
            // district, the same spot every build), and all seven are shot at
            // noon in rain 0.90 — one hour, one weather, seven samples, so
            // 0.020 + 0.020*0.90 = 0.038 of amplitude produced that row. The
            // worst of them against the reference ceiling is 7.51 / 2.05 =
            // 3.66, so a quarter puts the whole row inside the band the
            // references describe, with margin for the 5.21..7.51 the row
            // itself spans.
            //
            // LINEAR IN THE AMPLITUDE, MEASURED RATHER THAN SUPPOSED: uniform
            // noise of amplitude a, sRGB-encoded over the district ground
            // band's own luma and read back with ref-bench's own estimator,
            // falls 3.80x (mid luma) to 4.65x (the dark end, where the encode
            // is steep and the negative half clips at zero) for a 4x cut in
            // a. Four is therefore the conservative end of that range and the
            // districts should land at 1.1..1.9.
            //
            // WHAT JUDGES THIS: `grainSigma` in ref-bench on the next
            // landing, read across all seven districts. It is NOT a
            // closed-form calibration — the stills are JPEG q60 and DCT
            // quantisation attenuates a per-pixel noise field non-linearly
            // (measured: a flat synthetic field loses 45% of its sigma to q60
            // at the old amplitude and 92% at the new one), so the landed
            // number may fall further than the ratio alone predicts. If it
            // lands under the reference floor of 0.23 the cut was too deep
            // and the next number comes off that series, not off an argument.
            //
            // ONE GLOBAL EXPRESSION SCALES DAY AND NIGHT ALIKE. There is no
            // separate night amplitude to set: the noir shape is preserved
            // exactly — grain still rises with the dark and with the rain,
            // at a quarter the size. So the night frames stay above the
            // reference band on purpose (day2_night 9.15 → ~2.3, the wet
            // night day2_wet 13.12 → ~3.3), because all five references are
            // daylight or dusk and there is no night reference to judge a
            // night frame against. Trimming the night term further would be
            // choosing a number with nothing to check it, which is the thing
            // rule 2 forbids; getting a night reference frame is the fix and
            // it belongs on the queue, not here.
            //
            // THE TWIN: `SimDirector`'s grain gate derives its floor from
            // this same day amplitude (`const double GrainAmplitude`). It
            // moved with this change — a floor left at the old amount is a
            // tuned constant wearing a derivation's clothes.
            float grain = (0.0050f + 0.0055f * night + 0.0050f * Weather.Rain) * s.GrainAmount;
            // LAST-WINS, plus the run's span. Recorded here rather than at
            // the `SetFloat` below so it is the AUTHORED amount and not what
            // the A/B switch let through — see the field's own comment.
            LastGrain = grain;
            if (GrainLo < 0 || grain < GrainLo) GrainLo = grain;
            if (grain > GrainHi) GrainHi = grain;
            // FROM CORE, where it is stated as "how dark are the corners"
            // and tested. The 0.34/0.16 that used to live here put the
            // corners at 10% of centre by day and at exactly zero at night —
            // a black frame border rather than a vignette — and halved the
            // mean luminance of every frame. It had never been applied to an
            // image, because until tonight this class never ran.
            // THE FRAME BREATHES WITH THE LIGHT ON THE PLAYER, not just with
            // the hour. This is the whole of the visibility readout: no icon,
            // no meter, no word "detected" anywhere. Step under a lamp and the
            // corners lift; step into a doorway and they close in.
            float vignette = (float)LightModel.VignetteParamLit(night, LitAmount);
            // THE STANDOFF, and it is the only thing other than the light that
            // is allowed to touch this number. Four tenths of a second of the
            // frame closing in, once per person, for the moment somebody meets
            // your eye and you both know it.
            vignette += Standoff.FrameTighten * Standoff.Curve * vignette;

            // THE PRESET'S SHARE OF THE STACK (Core/Detail.PostBloom /
            // PostOcclusion carry the design). The sim is pinned to High, so
            // every still and every A/B gate renders the full stack — the
            // per-effect switches below this stay the sim's own instruments.
            var preset = Ledger.Core.Detail.Parse(GameSettings.Current.Detail);
            bool presetBloom = Ledger.Core.Detail.PostBloom(preset);

            // BLOOM: downsample, blur, add back. Two small textures rather
            // than a chain — at this scale the extra passes buy nothing you
            // can see, and every one costs a frame budget we have already
            // measured as tight. On Low the three passes are not run at all,
            // not run-and-multiplied-away.
            if (presetBloom)
            {
                int w = Mathf.Max(2, src.width / 4), h = Mathf.Max(2, src.height / 4);
                _bloomA = RenderTexture.GetTemporary(w, h, 0, src.format);
                _bloomB = RenderTexture.GetTemporary(w, h, 0, src.format);
                // FROM CORE, and it moves with the night. A fixed 0.62 under an
                // exposure that opens after dark meant the bright pass was
                // selecting most of the frame, which is a second exposure rather
                // than a highlight pass.
                _mat.SetFloat("_Threshold", (float)LightModel.BloomThreshold(night));
                Graphics.Blit(src, _bloomA, _mat, 1);            // pass 1: bright pass
                _mat.SetVector("_Dir", new Vector4(1f / w, 0, 0, 0));
                Graphics.Blit(_bloomA, _bloomB, _mat, 2);        // pass 2: blur X
                _mat.SetVector("_Dir", new Vector4(0, 1f / h, 0, 0));
                Graphics.Blit(_bloomB, _bloomA, _mat, 2);        // pass 2: blur Y
                _mat.SetTexture("_BloomTex", _bloomA);
            }
            else
            {
                _bloomA = _bloomB = null;
                _mat.SetTexture("_BloomTex", Texture2D.blackTexture);
            }
            _mat.SetFloat("_Bloom",
                Bloom && presetBloom ? (float)LightModel.BloomStrength(night) : 0f);
            _mat.SetFloat("_Grain", Grain ? grain : 0f);
            _mat.SetFloat("_Vignette", Vignette ? vignette : 0f);
            // The aperture opens at night and closes in daylight rain, from
            // the same curve the scene lighting uses.
            _mat.SetFloat("_Exposure",
                (float)Ledger.Core.LightModel.Exposure(night, Weather.Rain) * ExposureScale);
            // EXPOSED COOLS, HIDDEN WARMS — the only prospective signal in the
            // grade, and it has never once run.
            //
            // `LightModel.TemperatureFor` has sat on the reach ledger since it
            // was written, with a comment stating exactly what it is for:
            // *"under one percent, which is under the threshold at which
            // anyone consciously notices a tint and well over the threshold at
            // which they feel one."* Written, tested, and connected to
            // nothing.
            //
            // `LitAmount` is already here — `PlayerController` refreshes it
            // every frame from the real light on the player, and the vignette
            // two lines up has been reading it for weeks. So the input was
            // wired, the model was written, and the one line between them was
            // missing: the same shape as the seconds and the rung, an hour
            // ago, in a different system.
            var (tempR, tempB) = Ledger.Core.LightModel.TemperatureFor(LitAmount);
            _mat.SetFloat("_TempR", (float)tempR);
            _mat.SetFloat("_TempB", (float)tempB);
            LastTempR = tempR; LastTempB = tempB;

            // THE FINISH (M17.10): split-tone by day, a milky blue-black
            // floor by night, chroma draining with distance. All three ride
            // GameController.NightAmount — the one clock dusk already runs
            // on — and the desat is ZEROED whenever DepthNormals is off, so
            // the shader never reads an unbound depth texture on Low.
            float night01 = GameController.NightAmount;
            _mat.SetFloat("_SplitAmt", Mathf.Lerp(1.0f, 0.45f, night01));
            // 0.045 → 0.004 (V1.5, the ladder's verdict). The night-floor
            // A/B read all:0.256 / noLift:0.141 — this one additive constant
            // held nearly HALF the night mean, because it was authored for a
            // display-space framebuffer and the flip made the buffer linear:
            // post-tonemap +0.045 linear encodes to ~+0.23 sRGB in the
            // blacks, five times its intent. 0.004 linear encodes to ~0.05
            // display, which is the milky floor the grade wanted. The lamps
            // the last round trimmed contributed 0.008 of mean — innocent.
            _mat.SetFloat("_LiftAmt",
                Lift ? 0.004f * Mathf.SmoothStep(0f, 1f, night01) : 0f);
            bool depthBound = Ledger.Core.Detail.PostOcclusion(
                Ledger.Core.Detail.Parse(GameSettings.Current.Detail));
            _mat.SetFloat("_DesatFar", depthBound ? 0.18f : 0f);
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
            if (AmbientOcclusion && Ledger.Core.Detail.PostOcclusion(preset)
                && _cam != null && _ao != null)
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
                // FROM `LightModel`, NOT FROM TWO LITERALS HERE.
                //
                // These were `0.65f` and `0.35f` written out, and they are
                // `AoDirectRelief`'s coefficient and `AoMultiplier`'s clamp —
                // the same two numbers, in the tested C# model that has no
                // caller and in the code that actually reaches the frame. So
                // the copy with CoreTests behind it could be edited freely
                // while the render kept the old values, which is the drift the
                // reach ledger's AO entries now describe.
                _mat.SetFloat("_AoRelief", (float)LightModel.AoReliefAtFullLight);
                _mat.SetFloat("_AoFloor", (float)LightModel.AoFloor);
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
            if (_bloomA != null) RenderTexture.ReleaseTemporary(_bloomA);
            if (_bloomB != null) RenderTexture.ReleaseTemporary(_bloomB);
        }
    }
}
