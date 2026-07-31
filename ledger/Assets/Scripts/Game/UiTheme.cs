using Ledger.Core;
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
        /// Accessibility text scaling (P4). The Options slider set
        /// TextScalePercent, saved it, reloaded it — and nothing ever multiplied
        /// a font size by it. Every MakeText in the game now goes through here,
        /// so the control reaches the thing it names.
        // THE TYPE SCALE (Core/Typography). Sizes across the panels were 14,
        // 15, 18, 19, 22, 24, 64 — arbitrary numbers chosen one at a time,
        // which is what makes a competent interface look amateur even when
        // every individual screen is fine. Hierarchy comes from a SYSTEM or
        // it does not come at all.
        //
        // Each one already carries the accessibility scaling, so a call site
        // asks for a ROLE and gets the right number for this player.
        public static int Micro   => Scaled(Typography.Micro);
        public static int Small   => Scaled(Typography.Small);
        public static int Body    => Scaled(Typography.Body);
        public static int Lede    => Scaled(Typography.Lede);
        public static int Title   => Scaled(Typography.Title);
        public static int Display => Scaled(Typography.Display);
        public static int Hero    => Scaled(Typography.Hero);

        /// Eight-point rhythm. Every margin and gap is a multiple of it.
        public static int Space(double units) => Typography.Space(units);

        /// The widest a column of prose may be at a given size before the eye
        /// starts losing the return sweep. Panels are laid out to fixed
        /// widths here, so this is what keeps a wide one from becoming a
        /// hundred-character line.
        public static float MaxProseWidth(int points) =>
            (float)Typography.MaxWidthPixels(points);

        public static int Scaled(int basePoints) =>
            UnityEngine.Mathf.Clamp(
                UnityEngine.Mathf.RoundToInt(basePoints * GameSettings.Current.TextScalePercent / 100f),
                8, 96);

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

        /// The name of the face this project ships, under `Assets/Resources`.
        /// Empty until M17.9 lands one.
        public const string ShippedFont = "LedgerSans";

        /// True when the game is drawing its own typeface rather than borrowing
        /// the machine's. Read by the sim gate, so "we ship a font" is a fact
        /// the build checks rather than a plan somebody remembers.
        public static bool UsingShippedFont { get; private set; }

        /// A FONT THIS PROJECT SHIPS, falling back to the machine's.
        ///
        /// The completeness audit on 2026-07-31 found this borrowing Segoe UI
        /// from the OS, and that is wrong in two separate ways that both look
        /// like nothing:
        ///
        ///   Segoe UI is licensed by Microsoft and is not redistributable. The
        ///   game does not redistribute it — it asks the OS for it — so this is
        ///   legal, and it is also why THE TYPOGRAPHY DIFFERS PER MACHINE. On
        ///   macOS and Linux it falls through to Arial or Unity's legacy face,
        ///   so every measurement `Core/Typography` makes about line length and
        ///   contrast is made about a font that may not be the one on screen.
        ///
        ///   And the credits cannot name a typeface, because there isn't one.
        ///
        /// The fix is a face under an open licence living in `Resources`, which
        /// is M17.9 and needs a CI fetch: `fonts.google.com` answers 000 through
        /// this container's proxy, exactly like every texture host. Until the
        /// file is there this returns the borrowed font and SAYS SO — a silent
        /// fallback is how the project ended up not knowing it had no font.
        public static Font LoadFont()
        {
            var shipped = Resources.Load<Font>(ShippedFont);
            if (shipped != null)
            {
                UsingShippedFont = true;
                return shipped;
            }
            UsingShippedFont = false;
            var f = Font.CreateDynamicFontFromOSFont(new[] { "Segoe UI", "Arial" }, 18);
            return f != null ? f : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        }
    }
}
