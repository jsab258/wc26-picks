using System;

namespace Ledger.Core
{
    /// GRAPHICS DETAIL, as a small number of honest presets.
    ///
    /// WHY THIS EXISTS NOW. CI runs on a machine with no GPU, so every frame
    /// time this project has ever measured came from a software rasteriser
    /// and means nothing. The real number arrives the first time somebody
    /// plays it — and until this file, if the answer was "it runs badly"
    /// there was no dial to turn. Not in the options screen, not anywhere.
    /// Diagnosing it would have cost a build cycle per guess, and the person
    /// with the slow machine could do nothing at all in the meantime.
    ///
    /// THREE LEVELS, NOT A PANEL OF SLIDERS. A settings screen offering
    /// shadow distance, probe resolution and volumetric step count asks the
    /// player to do the optimisation, and almost nobody knows which of those
    /// costs anything. Three presets that each say what they give up is a
    /// better trade, and it also means there are three configurations to test
    /// rather than a combinatorial space nobody covers.
    ///
    /// THE ORDER THEY GIVE THINGS UP IS THE DESIGN. Shafts and shadows go
    /// first because they are the expensive half of the look and the game is
    /// still legible without them. The CROWD goes last and never entirely —
    /// this is a game about being surrounded by people who know things about
    /// you, and a street emptied for frame rate is not a cheaper version of
    /// LEDGER, it is a different and worse game. Someone on weak hardware
    /// should lose the wet asphalt, not the witnesses.
    public enum DetailLevel
    {
        Low = 0,
        Medium = 1,
        High = 2,
    }

    public static class Detail
    {
        public const DetailLevel Default = DetailLevel.High;

        /// How far light shafts are drawn, in metres. Zero means none.
        ///
        /// The first thing to go, and by a distance. Three hundred and sixty
        /// volumetric cones is the single most expensive thing in the scene
        /// and the lamps still glow without them.
        public static double ShaftDistance(DetailLevel d) =>
            d == DetailLevel.Low ? 0
            : d == DetailLevel.Medium ? 55
            : 95;

        /// Shadow draw distance, metres.
        ///
        /// Never zero. A city with no shadows at all does not look cheap, it
        /// looks broken — objects stop being attached to the ground, which
        /// reads as a bug rather than as a setting.
        /// High is `LightModel.ShadowDistanceMetres`, not a second copy of
        /// it. That constant was tuned for a street rather than a landscape
        /// and there is no reason for the preset to disagree with it — a
        /// number written down twice is a number that drifts, which is
        /// exactly how the wet-road threshold got away from this project
        /// earlier tonight.
        public static double ShadowDistance(DetailLevel d) =>
            d == DetailLevel.Low ? 22
            : d == DetailLevel.Medium ? 45
            : LightModel.ShadowDistanceMetres;

        /// How far bodies keep their detail parts and cast shadows.
        public static double BodyDetailDistance(DetailLevel d) =>
            d == DetailLevel.Low ? 12
            : d == DetailLevel.Medium ? 22
            : 34;

        /// Whether wet surfaces get a reflection probe at all.
        public static bool Reflections(DetailLevel d) => d != DetailLevel.Low;

        /// The fraction of the walking crowd kept.
        ///
        /// PROTECTED, and this is the whole argument. Halving the crowd is
        /// the biggest single frame-time win available and it is the one
        /// thing that must not be taken — the street is the game. Even Low
        /// keeps three quarters of it, which is a saving worth having and
        /// still a populated street.
        public static double CrowdFraction(DetailLevel d) =>
            d == DetailLevel.Low ? 0.75
            : d == DetailLevel.Medium ? 0.9
            : 1.0;

        /// What this level gives up, for the options screen.
        ///
        /// Written as a loss rather than as a name, because "Low" tells the
        /// player nothing and "no reflections, shorter shadows" tells them
        /// exactly what they are buying with their frame rate.
        public static string Describes(DetailLevel d) =>
            d == DetailLevel.Low
                ? "No light shafts or reflections, short shadows. The street stays busy."
            : d == DetailLevel.Medium
                ? "Shorter light shafts and shadows. Reflections kept."
                : "Everything on.";

        /// A rough cost index, 0..1, used only to prove the presets are
        /// ordered — that each step down is genuinely cheaper rather than a
        /// relabelling. Weighted by what actually costs: the shafts dominate,
        /// shadows next, and the crowd contributes but is never the lever.
        public static double CostIndex(DetailLevel d)
        {
            double shafts = ShaftDistance(d) / 95.0;
            double shadows = ShadowDistance(d) / LightModel.ShadowDistanceMetres;
            double bodies = BodyDetailDistance(d) / 34.0;
            double crowd = CrowdFraction(d);
            return Feel.Clamp01(0.42 * shafts + 0.26 * shadows
                                + 0.20 * bodies + 0.12 * crowd);
        }

        public static DetailLevel Parse(int i) =>
            i <= 0 ? DetailLevel.Low : i == 1 ? DetailLevel.Medium : DetailLevel.High;
    }
}
