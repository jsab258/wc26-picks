using UnityEngine;

namespace Ledger.Game
{
    /// The approved visual language (player decision 2026-07-26): "Two Books"
    /// banking precision for every opened screen — dark green-black panels,
    /// hairline edges, credit green against debit red — while the in-world
    /// street layer (clock, toasts, prompts) keeps sodium-lamp amber.
    /// Warm world, cold books.
    public static class UiTheme
    {
        // The books (opened screens)
        public static readonly Color PanelBg   = Rgb(0x101514, 0.97f);
        public static readonly Color PanelDeep = Rgb(0x0c0f0e, 0.98f);
        public static readonly Color Hairline  = Rgb(0x2a3431, 1f);
        public static readonly Color Ink       = Rgb(0xe6ece8, 1f);
        public static readonly Color Dim       = Rgb(0x93a09a, 1f);
        // Credit/debit are the only hue-coded pair in the game, so they are the
        // only accessibility risk: red-green is the common deficiency. The
        // colourblind-safe set swaps to blue/orange, which survives every
        // common form, and the rich-text hexes follow.
        public static Color Credit = Rgb(0x4fc98c, 1f);
        public static Color Debit  = Rgb(0xe05252, 1f);

        public static void SetColourblind(bool on)
        {
            Credit = on ? Rgb(0x4aa3e0, 1f) : Rgb(0x4fc98c, 1f);
            Debit = on ? Rgb(0xe08a30, 1f) : Rgb(0xe05252, 1f);
            HexCredit = on ? "#4aa3e0" : "#4fc98c";
            HexDebit = on ? "#e08a30" : "#e05252";
        }
        // The street (world HUD)
        public static readonly Color Amber     = Rgb(0xffa636, 1f);
        public static readonly Color AmberSoft = Rgb(0xffc272, 1f);
        // Controls
        public static readonly Color Field     = Rgb(0x0d1110, 1f);
        public static readonly Color ButtonBg  = Rgb(0x1c2422, 1f);

        // The same system for inline rich-text markup.
        public const string HexDim    = "#93a09a";
        public static string HexCredit = "#4fc98c";
        public static string HexDebit  = "#e05252";
        public const string HexHeld   = "#7f8c86";
        public const string HexAmber  = "#ffa636";

        static Color Rgb(int rgb, float a) =>
            new Color(((rgb >> 16) & 0xFF) / 255f, ((rgb >> 8) & 0xFF) / 255f, (rgb & 0xFF) / 255f, a);

        /// Segoe UI where the OS has it (every Windows target), else the engine's
        /// built-in face. One family, weights via rich text — the Two Books way.
        public static Font LoadFont()
        {
            var f = Font.CreateDynamicFontFromOSFont(new[] { "Segoe UI", "Arial" }, 18);
            return f != null ? f : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        }
    }
}
