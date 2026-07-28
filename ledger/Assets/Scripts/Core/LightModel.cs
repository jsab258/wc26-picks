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
            // Rain takes light out of the sky in the day and puts it back at
            // night, because everything wet reflects the lamps.
            double e = 1.0 + 0.55 * night - 0.15 * rain * (1 - night) + 0.10 * rain * night;
            return Feel.Clamp(e, 0.7, 1.8);
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
            var (hr, hg, hb) = HorizonColour(night, rain);
            // Slightly brighter than the horizon and pulled toward the lamps,
            // because fog is lit from inside the scene rather than from the
            // sky.
            double warm = 0.65 * Feel.Clamp01(night);
            return (Feel.Clamp01(hr * 1.15 + 0.055 * warm),
                    Feel.Clamp01(hg * 1.10 + 0.032 * warm),
                    Feel.Clamp01(hb * 1.05 + 0.010 * warm));
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
