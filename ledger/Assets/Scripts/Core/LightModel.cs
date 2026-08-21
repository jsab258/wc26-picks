using System;

namespace Ledger.Core
{
    /// THE LIGHTING MODEL (the-gap.md §3a).
    ///
    /// The single cheapest large win available to this project. KCD2 looks
    /// like KCD2 mostly because of LIGHT AND MATERIALS rather than geometry,
    /// and a rainy night street with volumetric lamp cones on wet asphalt
    /// reads as expensive over box geometry — which is exactly the setting
    /// LEDGER already has.
    ///
    /// All of it lives here rather than in the Unity layer for the usual
    /// reason: the curves are where the look is decided, and a curve nobody
    /// can test is a curve that drifts. What Unity gets is the numbers.
    ///
    /// One rule the whole file is built on: **a light model that clips is a
    /// light model that loses colour.** The neon defect earlier this month
    /// was exactly that, one level down — a multiply that pushed channels
    /// past 1.0 and turned four coloured signs white. Everything here either
    /// tone-maps or stays in range by construction.
    public static class LightModel
    {
        // ---- tone mapping -------------------------------------------------

        /// ACES filmic curve (Narkowicz's fit), per channel.
        ///
        /// This is the difference between "a game with bright lights in it"
        /// and "a photograph of a street". A linear clamp takes every value
        /// over 1.0 and makes it white, which is how a red neon sign becomes
        /// a white rectangle. A filmic curve ROLLS OFF instead: highlights
        /// compress, hue survives, and the eye reads the result as exposure
        /// rather than as damage.
        public static double Aces(double x)
        {
            if (x <= 0) return 0;
            const double a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
            double y = (x * (a * x + b)) / (x * (c * x + d) + e);
            return Feel.Clamp01(y);
        }

        /// How much light to let in. Night is LIFTED rather than left dark:
        /// a real eye adapts, and a player who cannot see the street is not
        /// experiencing atmosphere, they are experiencing a bug report.
        public static double Exposure(double night, double rain = 0)
        {
            night = Feel.Clamp01(night);
            // THE NIGHT LIFT WAS 0.55 AND IT HAD NEVER BEEN APPLIED TO
            // ANYTHING. The post stack was attached to a child of the camera
            // and never ran, so this number was authored, reasoned about, and
            // never once looked at. The first frame it touched came out
            // BRIGHTER at midnight than at midday — 0.099 against 0.088 in
            // CI — which is the one thing a night must not be.
            //
            // It went 0.55 -> 0.10 -> BELOW ZERO, and each step was the same
            // argument applied to a street with more real light in it than
            // the last time anyone measured.
            //
            // 0.55 was sized for an unlit street. 0.10 was sized for a street
            // with three hundred and sixty light shafts. This one also has
            // wet asphalt that genuinely reflects the lamps — the reflection
            // probe lit nothing at all until this morning, and now puts
            // measurable light back into fourteen percent of a night frame.
            // Night came out BRIGHTER than noon again, 0.137 against 0.131,
            // and the aperture was the only thing left holding it up.
            //
            // So it stops down at night now rather than opening up. THE LAMPS
            // DO THE LIFTING, and they finally reflect. A night street lit by
            // its own lamps and their reflections is the thing the whole
            // lighting pass was for; opening the aperture on top of that is
            // paying twice for light we already have, and it costs the one
            // property a night must keep.
            // AND THE DAY OPENS UP, which is the half I missed first time.
            //
            // Stopping night down brought it from 0.137 to 0.117 — and noon
            // was 0.117 too. Dead equal. The reading that matters is not that
            // the night was too bright, it is that a MIDDAY street and a
            // MIDNIGHT one were being exposed identically, which no camera
            // and no eye has ever done. Crushing the night further would have
            // hidden that behind a number that passed.
            //
            // So the aperture now moves in both directions around noon, and
            // the gap between them is the thing being asserted rather than
            // either end.
            // Day term 0.12 → 0.28 (M17.10, after the shadow batch landed).
            // The ambient share and shadow strength changes pulled the noon
            // scene mean 0.289 → 0.252 → 0.205 across three landed builds —
            // the shade got RIGHT and the lit surfaces sank with it, which is
            // the opposite of the reference: GTA noon is bright with deep
            // shade, not dim with deep shade. Opening the day aperture
            // restores the lit side while the shadowed:lit RATIO — the thing
            // the whole rebalance was for, measured at 0.21 mean drop over
            // 57% of pixels — rides the light, not the exposure, and keeps.
            // Night terms untouched; the noon/night gap widens, which is the
            // direction every instrument wants.
            // LINEAR COLOUR SPACE RE-ARM (M17.10 V1.5, the retune half).
            // The flip's own A/B, two landed builds apart with only the flip
            // between them, moved both ends the wrong way: noon scene mean
            // fell 0.205 -> 0.172 while the night AO pass's off-mean rose
            // 0.092 -> 0.255 — a NIGHT brighter than its own NOON, failing
            // the one bound this function's history keeps re-learning. The
            // gamma curve had been quietly lifting mid-tones for every
            // number here; in linear the day arm buys less and the night's
            // window emissives buy far more.
            //
            // Day up, sized from the measured ratio (restore noon ~0.24).
            // The night arm stops down only to the TESTED floor — the first
            // draft went to 0.58 and the CoreTests bound at 0.85 refused it,
            // correctly: the night's excess is mostly the gamma-authored
            // window emissives running hot in linear, and crushing the
            // aperture past its floor would buy their fix by darkening the
            // unlit corners the floor exists to protect. The emissives are
            // dimmed at their source instead (WindowGlow).
            // Round two, from round one's measured response: +0.24 of day
            // arm bought +0.023 of noon mean (0.172 -> 0.195, target ~0.24)
            // — the tonemap rolls off, so the arm buys less than linear.
            // Up again with the clamp raised to let it land; night arm still
            // floor-bound, its remaining excess handled at the sources
            // (WindowGlow round two, grain round two).
            double e = 1.0 + 0.72 * (1 - night) - 0.14 * night
                       - 0.15 * rain * (1 - night) + 0.06 * rain * night;
            return Feel.Clamp(e, 0.7, 1.85);
        }

        // ---- bloom ----------------------------------------------------------

        /// THE THIRD NUMBER AUTHORED WHILE THE POST STACK WAS DEAD, and the
        /// one that blew the night out: 0.549 mean luminance at midnight
        /// against 0.159 at noon, on the first frame it was ever applied to.
        ///
        /// Bloom is ADDED before the tonemap, so it compounds with everything
        /// else rather than replacing it. Kept low, and — the part that is
        /// not obvious — kept LOWER at night than by day, because this city
        /// already has three hundred and sixty light shafts. The glow around
        /// a lamp is geometry here. Blooming it again is counting it twice.
        public static double BloomStrength(double night)
        {
            return Mix(0.34, 0.26, Feel.Clamp01(night));
        }

        /// WHAT COUNTS AS A HIGHLIGHT, and this is where the real defect was.
        ///
        /// The threshold was a fixed 0.62 while the exposure moves with the
        /// hour. Open the aperture and more of the image crosses any fixed
        /// line — so at night a threshold meant to catch "the lamps" was
        /// catching lamps, wet road, shafts, windows and most of the sky. A
        /// bright pass that selects half the frame is not a bright pass, it
        /// is a second exposure.
        ///
        /// It rises with the night so that it keeps meaning the same thing:
        /// the top few percent of the image, whatever the aperture is doing.
        public static double BloomThreshold(double night)
        {
            return Mix(0.62, 0.88, Feel.Clamp01(night));
        }

        // ---- the vignette --------------------------------------------------

        /// THE CORNERS WERE GOING TO ZERO. Not dimmed — zero.
        ///
        /// The shader computes `v = 1 - dot(d,d) * V * 4` and multiplies by
        /// `v*v`, where `d` is the offset from centre and reaches 0.5 squared
        /// at a corner. With the authored V of 0.34 by day that put the
        /// corners at 10% of centre; at night V rose to 0.50 and put them at
        /// EXACTLY NOTHING. That is a black frame border, not a vignette, and
        /// it halved the mean luminance of every frame in the game.
        ///
        /// Same root cause as the exposure above: authored while the post
        /// stack was dead, so nobody — including me — had ever seen it.
        ///
        /// Stated here as the CORNER FACTOR, which is the thing anybody
        /// actually has an opinion about, with the shader parameter derived
        /// from it. A number expressed as "how dark are the corners" can be
        /// argued with; one expressed as a coefficient inside a quadratic
        /// cannot.
        public const double VignetteCornerDay = 0.72;
        public const double VignetteCornerNight = 0.62;

        /// The corner brightness we want, 0..1 of centre.
        public static double VignetteCorner(double night) =>
            Mix(VignetteCornerDay, VignetteCornerNight, Feel.Clamp01(night));

        /// The shader's `_Vignette`, solved from the corner we asked for.
        ///
        /// At a corner `dot(d,d)` is 0.5, so `v = 1 - 2V` and the applied
        /// factor is `v*v`. Inverting: `V = (1 - sqrt(corner)) / 2`.
        public static double VignetteParam(double night)
        {
            double v = Math.Sqrt(Feel.Clamp01(VignetteCorner(night)));
            return Feel.Clamp((1.0 - v) / 2.0, 0, 0.49);
        }

        // ---- EXPOSURE AS A READOUT (weapons-spec.md §6.2) -----------------
        //
        // THE ONE PROSPECTIVE SIGNAL THE PLAYER GETS, and the reason it lives
        // here rather than in a HUD: Tom Novak runs a bar, he does not have an
        // interface, and a stealth-adjacent system the player cannot predict
        // is not immersive, it is unfair. Thief put a gem on the screen for a
        // reason and we cannot.
        //
        // So the frame itself carries it. Lit and exposed: the vignette OPENS
        // and the image cools very slightly. In shadow: it CLOSES and warms.
        // Sub-threshold in a screenshot, learnable inside an hour of play, and
        // it never once says the word "detected".
        //
        // Deliberately small. Conviction went to full desaturation, which is
        // the loud version of this idea; ours is about a tenth as strong
        // because it has to coexist with a wet-asphalt night the art pass
        // spent a week on.

        /// How much the corner darkening moves with exposure, as a fraction of
        /// the base corner. Small enough to be invisible in a still frame and
        /// large enough that `ImageStats` can prove it happened.
        public const double VignetteLightSwing = 0.10;

        /// The corner brightness given both the hour AND how lit the player
        /// is. `lightOnPlayer` is the same 0..1 the perception model uses, so
        /// the two halves of the symmetry rule come from one source rather
        /// than from two numbers that can drift apart.
        public static double VignetteCornerLit(double night, double lightOnPlayer)
        {
            double baseCorner = VignetteCorner(night);
            // Lit -> corners lift (the frame opens). Dark -> corners close in.
            double swing = VignetteLightSwing * (Feel.Clamp01(lightOnPlayer) * 2.0 - 1.0);
            return Feel.Clamp(baseCorner * (1.0 + swing), 0.35, 0.95);
        }

        public static double VignetteParamLit(double night, double lightOnPlayer)
        {
            double v = Math.Sqrt(Feel.Clamp01(VignetteCornerLit(night, lightOnPlayer)));
            return Feel.Clamp((1.0 - v) / 2.0, 0, 0.49);
        }

        /// Colour temperature nudge, as a multiplier on the red and blue
        /// channels. Exposed cools; hidden warms. Under one percent, which is
        /// under the threshold at which anyone consciously notices a tint and
        /// well over the threshold at which they feel one.
        public const double TemperatureSwing = 0.008;

        public static (double r, double b) TemperatureFor(double lightOnPlayer)
        {
            double t = (Feel.Clamp01(lightOnPlayer) * 2.0 - 1.0) * TemperatureSwing;
            return (1.0 - t, 1.0 + t);   // lit: less red, more blue
        }

        /// What the shader will actually multiply by, at squared-radius `dd`
        /// from centre (0 at the middle, 0.5 at a corner). Mirrors the shader
        /// exactly so the test is testing the shipped arithmetic.
        public static double VignetteAt(double dd, double night)
        {
            double v = Feel.Clamp01(1.0 - Feel.Clamp(dd, 0, 0.5) * VignetteParam(night) * 4.0);
            return v * v;
        }

        // ---- the sky ------------------------------------------------------

        /// Ambient light comes in three bands — sky, horizon, ground — and
        /// using one flat colour for all three is the thing that makes an
        /// untextured scene look like an untextured scene. The sky is cool,
        /// the horizon carries the sun or the sodium haze, the ground is
        /// warm-dark from bounced street light.
        public static (double r, double g, double b) SkyColour(double night, double rain = 0)
        {
            night = Feel.Clamp01(night); rain = Feel.Clamp01(rain);
            // Day: a pale, slightly cool overcast. Night: deep blue, never
            // black — a black sky reads as a missing skybox.
            double r = Mix(0.55, 0.045, night);
            double g = Mix(0.62, 0.055, night);
            double b = Mix(0.72, 0.105, night);
            return Desaturate(r, g, b, 0.35 * rain);
        }

        public static (double r, double g, double b) HorizonColour(double night, double rain = 0)
        {
            night = Feel.Clamp01(night); rain = Feel.Clamp01(rain);
            // The band that does the work. At night this is the sodium glow
            // of a city bouncing off low cloud, and it is what stops the
            // middle distance going to a flat void.
            double r = Mix(0.58, 0.135, night);
            double g = Mix(0.58, 0.095, night);
            double b = Mix(0.60, 0.080, night);
            return Desaturate(r, g, b, 0.25 * rain);
        }

        public static (double r, double g, double b) GroundColour(double night, double rain = 0)
        {
            night = Feel.Clamp01(night); rain = Feel.Clamp01(rain);
            double r = Mix(0.30, 0.050, night);
            double g = Mix(0.28, 0.045, night);
            double b = Mix(0.26, 0.048, night);
            return Desaturate(r, g, b, 0.20 * rain);
        }

        // ---- ambient fill, SEPARATED from the sky dome (M17.10 V1) --------

        /// THE AMBIENT IS NOT THE SKY, and one function was feeding both.
        ///
        /// `SkyColour`/`HorizonColour`/`GroundColour` are used twice over:
        /// painted onto the skybox dome (where their honest daytime
        /// brightness is correct — an overcast sky IS bright) and written
        /// into `RenderSettings.ambient*` as the diffuse fill on every
        /// surface. Reusing the dome brightness as fill put daytime ambient
        /// luma around 0.6 against a sun of 1.15 — a shaded pixel kept most
        /// of a lit pixel's light, which is why the noon still shows no
        /// shadow anyone can point at and why the AO pass, whose relief
        /// deliberately backs off on bright pixels, measured 0.7% of frame
        /// luma. The GTA V reference noon is strongly directional: the fill
        /// is a fraction of the key.
        ///
        /// So the ambient WRITES get their own accessors: same hues, same
        /// night values (night ambient was tuned AS ambient and is kept
        /// bit-identical), with the DAY portion scaled to `AmbientDayShare`
        /// of the dome. Rain lifts the share back toward the dome, because
        /// overcast really is a big soft source — that is frame 3 of the
        /// reference set, where AO and surface detail carry the image.
        /// 0.60 → 0.45 same day, off the technique research rather than my
        /// first guess: worked through the shipped tonemap's own constants,
        /// share 0.60 with the new sun lands the shadowed:lit display ratio
        /// near 0.69 — a visible shadow, but above the ~0.45-0.55 band read
        /// off the GTA reference noons, where a cast shadow is roughly HALF
        /// the lit brightness. 0.45 with shadow strength 0.93 computes to
        /// ~0.5. The probe's shadowHit/shadowDrop plus the stills judge it.
        public const double AmbientDayShare = 0.45;

        static (double r, double g, double b) AmbientOf(
            (double r, double g, double b) dome, double night, double rain)
        {
            night = Feel.Clamp01(night); rain = Feel.Clamp01(rain);
            // Day share rises toward 1.0 with rain; night is left alone.
            double share = Mix(Mix(AmbientDayShare, 0.95, rain), 1.0, night);
            return (dome.r * share, dome.g * share, dome.b * share);
        }

        public static (double r, double g, double b) AmbientSky(double night, double rain = 0)
            => AmbientOf(SkyColour(night, rain), night, rain);

        public static (double r, double g, double b) AmbientHorizon(double night, double rain = 0)
            => AmbientOf(HorizonColour(night, rain), night, rain);

        public static (double r, double g, double b) AmbientGround(double night, double rain = 0)
            => AmbientOf(GroundColour(night, rain), night, rain);

        // ---- fog ----------------------------------------------------------

        /// Exponential-squared density. Fog is not weather here, it is DEPTH
        /// CUEING: it separates near from far, which is the thing that makes
        /// a street feel like it continues past what you can see. Without it
        /// every building sits at the same apparent distance.
        public static double FogDensity(double night, double rain = 0)
        {
            night = Feel.Clamp01(night); rain = Feel.Clamp01(rain);
            // Thick enough to read, thin enough to see the far side of the
            // street. Rain roughly doubles it; night adds a little haze.
            return 0.0085 + 0.0060 * night + 0.0130 * rain;
        }

        /// Fog takes the colour of what is lighting it, which is why a night
        /// fog under sodium lamps is warm and a day fog is not. Getting this
        /// wrong — grey fog at night — is the single most common way a scene
        /// reads as "untextured game" rather than "photograph".
        public static (double r, double g, double b) FogColour(double night, double rain = 0)
        {
            night = Feel.Clamp01(night); rain = Feel.Clamp01(rain);
            // THE DAY ARM IS THE CALIBRATED ONE, MOVED HERE FROM THE WRITER
            // THAT WAS LOSING (M17.10). Two systems wrote fog every frame:
            // GameController in Update carried these calibrated values — the
            // "sky at ~1.8x the scene mean, not 2.6x" fix — and SceneLighting
            // in LateUpdate overwrote them with this function's old output.
            // The comment beside the calibration claimed GameController "runs
            // last"; Update runs BEFORE LateUpdate, so the calibration
            // reached only the probes that render mid-Update, and the
            // composited frame kept the old bright sky. One owner now: this
            // function carries both arms, and nothing else writes fog.
            //
            // Cool overcast day, pulled slightly flatter and cooler when wet
            // (a wet noon must not jump brighter than a clear one).
            double dr = Mix(0.415, 0.401, rain);
            double dg = Mix(0.446, 0.421, rain);
            double db = Mix(0.484, 0.442, rain);

            // The night arm is unchanged: slightly brighter than the horizon
            // and pulled toward the lamps, because night fog is lit from
            // inside the scene rather than from the sky — the CoreTest that
            // holds it warmer than the horizon is the guard.
            var (hr, hg, hb) = HorizonColour(1.0, rain);
            double nr = Feel.Clamp01(hr * 1.15 + 0.055 * 0.65);
            double ng = Feel.Clamp01(hg * 1.10 + 0.032 * 0.65);
            double nb = Feel.Clamp01(hb * 1.05 + 0.010 * 0.65);

            return (Mix(dr, nr, night), Mix(dg, ng, night), Mix(db, nb, night));
        }

        // ---- volumetrics --------------------------------------------------

        /// Beer–Lambert transmittance: how much of a light survives `metres`
        /// of participating medium. What is left over is what you SEE as the
        /// cone — so this one function is both the shaft and the falloff.
        public static double Transmittance(double metres, double density)
        {
            if (metres <= 0 || density <= 0) return 1.0;
            return Math.Exp(-metres * density);
        }

        /// Henyey–Greenstein phase function: fog scatters FORWARD, so a lamp
        /// glows far more when you look toward it than away from it.
        ///
        /// This asymmetry is the entire reason volumetric light looks like
        /// light rather than like a translucent cone-shaped object. An
        /// isotropic version (g = 0) is a uniform haze and reads as fog on
        /// the lens.
        public static double Phase(double cosTheta, double g = 0.62)
        {
            g = Feel.Clamp(g, -0.95, 0.95);
            cosTheta = Feel.Clamp(cosTheta, -1, 1);
            double gg = g * g;
            // No guard on the denominator, and that is deliberate rather
            // than an oversight: g is clamped to 0.95 and cos to 1, so the
            // smallest value 1 + g^2 - 2g*cos can reach is 0.0025. A guard
            // here was written, tested against every (g, cos) pair on a fine
            // grid, and found to be dead code — the same fate as the
            // Curtain's alpha guard, and recorded for the same reason.
            double denom = 1.0 + gg - 2.0 * g * cosTheta;
            return (1.0 - gg) / (4.0 * Math.PI * Math.Pow(denom, 1.5));
        }

        /// A lamp cone's brightness at a point, before colour. `metres` is
        /// distance from the bulb, `cosTheta` is the view alignment, `spread`
        /// is 0..1 across the cone from axis to lip.
        public static double ConeBrightness(double metres, double range, double cosTheta,
                                            double edge, double density)
        {
            if (range <= 0 || metres >= range) return 0;
            // Inverse-square, softened near the bulb so it does not blow out
            // to infinity at zero distance.
            double falloff = 1.0 / (1.0 + metres * metres * 0.25);
            // Soft lip. A hard-edged cone is a cone-shaped OBJECT.
            double lip = Feel.Clamp01(1.0 - edge);
            lip = lip * lip;
            double reach = Feel.Clamp01(1.0 - metres / range);
            return falloff * lip * reach * Phase(cosTheta, 0.62) * density * 12.0;
        }

        // ---- surfaces -----------------------------------------------------

        /// WET ASPHALT, and the mistake worth naming because everybody makes
        /// it: wet ground is not just shinier, it is DARKER.
        ///
        /// A water film fills the surface micro-structure, so less light
        /// scatters back out (albedo down) and more reflects specularly
        /// (smoothness up). Raising smoothness alone gives a bright shiny
        /// road that reads as polished plastic. Dropping albedo at the same
        /// time is what makes the lamps' reflections POP off a dark road,
        /// which is the entire look of a rainy street at night.
        public static double Smoothness(double dry, double rain)
        {
            rain = Feel.Clamp01(rain);
            return Feel.Clamp01(dry + (0.92 - dry) * rain);
        }

        public static double AlbedoScale(double rain)
        {
            rain = Feel.Clamp01(rain);
            return Feel.Clamp(1.0 - 0.45 * rain, 0.55, 1.0);
        }

        /// Puddles do not appear the instant it rains and do not vanish the
        /// instant it stops. Ground stays wet after — which is free
        /// continuity, and the reason the street looks like it has a history
        /// half an hour later.
        public static double Wetness(double current, double rain, double seconds)
        {
            double target = Feel.Clamp01(rain);
            // Wets four times faster than it dries, like a real street.
            double k = target > current ? 0.35 : 0.085;
            return Feel.Clamp01(Feel.Approach(current, target, k, seconds));
        }

        // ---- reflections ---------------------------------------------------

        /// HOW MUCH THE WORLD SHOULD SHOW UP IN THE GROUND.
        ///
        /// Wet asphalt with high smoothness and nothing to reflect is just a
        /// shiny black surface — the specular highlight from a lamp, and
        /// nothing else. What makes a rainy street read is the NEON AND THE
        /// BUILDINGS appearing in it, upside down and broken up. That needs
        /// something sampling the surroundings, and something sampling the
        /// surroundings costs frames.
        ///
        /// So it is gated on being visible: a dry street in daylight gets
        /// none of it, because there is nothing to see and it would be paid
        /// for anyway.
        /// Below this a road counts as dry. ONE constant, used by both the
        /// early-out and the curve, because the two started as separate
        /// literals that happened to agree — and a break run proved that
        /// meant neither could be tested. Move the guard alone and the curve
        /// still returns zero; move the curve alone and the guard still
        /// returns zero. Each half silently covered for the other, so the
        /// threshold that decides whether a rained-on street looks wet was
        /// the one number here nothing could see change.
        public const double DryBelow = 0.12;

        /// (The early-out itself is a PERF skip, not a correctness gate — the
        /// curve clamps to zero below the threshold anyway, so deleting the
        /// `if` leaves every check green. It is there to avoid asking a probe
        /// to resample a dry road, and it stays.)

        public static double ReflectionStrength(double wetness, double night)
        {
            double w = Feel.Clamp01(wetness);
            if (w < DryBelow) return 0;
            // Night matters as much as wet: the same road reflects the same
            // amount at noon and nobody notices, because the sky is brighter
            // than anything in the reflection.
            return Feel.Clamp01((w - DryBelow) / (1 - DryBelow)) * (0.35 + 0.65 * Feel.Clamp01(night));
        }

        /// HOW OFTEN TO RESAMPLE, and the insight worth having: staleness is
        /// a function of HOW FAR YOU HAVE MOVED, not of how long it has been.
        ///
        /// A player standing still is looking at a reflection that is exactly
        /// correct and will stay correct, so refreshing it on a timer is
        /// paying every second for nothing. A player running down a street is
        /// looking at one that is wrong by a metre a frame. Distance is the
        /// thing that actually invalidates it.
        ///
        /// Returns metres of travel between refreshes.
        public const double ReflectionMetresPerRefresh = 6.0;

        /// And a floor in seconds, so a player spinning on the spot — which
        /// covers no distance and changes the whole view — still gets one.
        public const double ReflectionMaxStaleSeconds = 4.0;

        public static bool ShouldRefreshReflection(double metresSince, double secondsSince,
                                                   double strength)
        {
            if (strength <= 0) return false;
            return metresSince >= ReflectionMetresPerRefresh
                || secondsSince >= ReflectionMaxStaleSeconds;
        }

        // ---- shadows ------------------------------------------------------

        /// Shadow distance for a STREET rather than a landscape. Unity's
        /// default spends the whole cascade budget on ground the player will
        /// never look at, and the result is soft mush on the one thing they
        /// will — the person standing three metres away.
        public const double ShadowDistanceMetres = 70;

        // ---- ambient occlusion ---------------------------------------------

        /// AMBIENT OCCLUSION, and why it is the last cheap win: untextured
        /// geometry reads flat because nothing sits IN anything. A crate on a
        /// pavement, a bin against a wall, a person on a street — each is a
        /// shape floating in front of another shape, because the corner where
        /// they meet is lit exactly as brightly as the open ground.
        ///
        /// Contact darkening is what the eye uses to place objects on
        /// surfaces, and it is the single largest remaining difference
        /// between this render and a photographed one that costs no assets.
        ///
        /// The sampling itself lives in the shader. What lives HERE is every
        /// number that decides how it looks, so it is tested rather than
        /// tuned by eye in a file nobody can run.

        /// How far, in metres, a surface looks for things occluding it.
        /// Contact-scale, not room-scale: this is meant to darken the seam
        /// where two things meet, and a large radius produces a soft grey
        /// wash that reads as dirt.
        ///
        /// 0.55 → 0.85 for M17.10 V1: the reference frames carry visible
        /// darkening UNDER cars and INSIDE shop recesses, which are
        /// 0.5-1.0m cavities, not 10cm seams. The wash risk the paragraph
        /// above names is real and the aoDelta instrument in the sim is what
        /// decides — if the next run reads as smudge, this number comes back
        /// down, not the comment.
        public const double AoRadiusMetres = 0.85;

        /// HOW MUCH, from the light. Strong under a flat overcast or at
        /// night under fill, weak under hard sun — because AO is an
        /// approximation of ambient light being blocked, and when almost all
        /// the light is directional there is little ambient to block.
        /// Applying a constant amount is what makes cheap AO read as smudge.
        public static double AoStrength(double night, double rain)
        {
            double n = Feel.Clamp01(night), r = Feel.Clamp01(rain);
            // Overcast (rain) flattens daylight into ambient, so AO matters
            // MORE in the rain even at noon.
            //
            // Base 0.32 → 0.42 for M17.10 V1. The measured effect of the
            // whole pass was 0.00135..0.00694 of frame luma — invisible —
            // and most of that loss is the relief backing off on a frame
            // where the OLD ambient fill made every pixel bright. The
            // ambient share fix upstream does the heavy lifting; this base
            // raise is the second half, and the ceiling stays under the
            // CoreTests bound (0.42 + 0.38 = 0.80 < 0.85).
            double ambientness = Math.Max(n, r * 0.8);
            // The linear bracket, two rounds in: 0.42+0.38 read delta 0.028
            // with an 86.8% peak round (heavy), 0.30+0.30 read 0.0037
            // (invisible again) — the response is far steeper than the base
            // cut, so the midpoint is measured rather than assumed. Ceiling
            // 0.36 + 0.34 = 0.70, still under the CoreTests bound.
            return 0.36 + 0.34 * ambientness;
        }

        /// Whether a sample counts. A sample far in FRONT of the surface is
        /// a different object entirely, and counting it is what produces the
        /// dark halo around every silhouette that gives cheap SSAO away.
        public static double AoRangeCheck(double depthDeltaMetres, double radiusMetres)
        {
            double r = Math.Max(1e-6, radiusMetres);
            double d = Math.Abs(depthDeltaMetres);
            if (d <= r) return 1.0;
            // Falls off rather than cutting, or the halo becomes a hard edge
            // instead of a soft one.
            return Feel.Clamp01(1.0 - (d - r) / r);
        }

        /// AO RELIEF ON DIRECTLY-LIT PIXELS.
        ///
        /// A post-process pass cannot separate ambient light from direct, so
        /// multiplying the composited frame darkens a sunlit wall as much as
        /// a shaded corner — which is wrong, and is why so much screen-space
        /// AO looks like grime. Brightness is a decent proxy for "this pixel
        /// is directly lit", so the effect backs off as the pixel gets
        /// brighter. It is an approximation and it is stated as one.
        /// HOW MUCH RELIEF A FULLY-LIT PIXEL GETS, named because it is written
        /// in two places and only one of them is tested.
        ///
        /// `FilmGrade` pushes this same number into the shader as `_AoRelief`,
        /// hardcoded as `0.65f` beside a `_AoFloor` of `0.35f` — and those are
        /// this function's literal and `AoMultiplier`'s clamp. The C# half has
        /// CoreTests; the half that actually reaches the frame had a magic
        /// number. Editing one moved nothing and looked like a change.
        public const double AoReliefAtFullLight = 0.65;

        /// And never darker than this. An occlusion term reaching zero turns
        /// every interior corner into a hole, and no real corner is unlit.
        public const double AoFloor = 0.35;

        public static double AoDirectRelief(double luminance)
        {
            return 1.0 - AoReliefAtFullLight * Feel.Clamp01(luminance);
        }

        /// The final multiplier applied to a pixel. `raw` is 0 (fully open)
        /// to 1 (fully enclosed).
        public static double AoMultiplier(double raw, double strength, double luminance)
        {
            double a = Feel.Clamp01(raw) * Feel.Clamp01(strength) * AoDirectRelief(luminance);
            return Feel.Clamp(1.0 - a, AoFloor, 1.0);
        }

        // ---- helpers ------------------------------------------------------

        static double Mix(double a, double b, double t) => a + (b - a) * Feel.Clamp01(t);

        /// Rain does not add grey — it takes SATURATION out, which is a
        /// different and much better-looking thing.
        static (double, double, double) Desaturate(double r, double g, double b, double amount)
        {
            amount = Feel.Clamp01(amount);
            double lum = 0.299 * r + 0.587 * g + 0.114 * b;
            return (Mix(r, lum, amount), Mix(g, lum, amount), Mix(b, lum, amount));
        }
    }
}
