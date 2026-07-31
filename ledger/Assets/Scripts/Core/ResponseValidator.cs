using System;

namespace Ledger.Core
{
    /// §9 guardrails, output side: every LLM reply passes through here before the
    /// player sees it. Two jobs only — keep replies conversation-sized (truncate
    /// at a sentence boundary), and never let a character break the fourth wall
    /// (break markers are replaced with an in-character deflection, because a
    /// visible glitch in a person is worse than a dodged question).
    public static class ResponseValidator
    {
        public const int MaxChars = 900;

        static readonly string[] BreakMarkers =
        {
            "as an ai", "language model", "system prompt", "i cannot roleplay",
            "i'm an assistant", "i am an assistant", "my instructions", "as a chatbot",
        };

        public static string Validate(string reply, string characterName)
        {
            if (string.IsNullOrWhiteSpace(reply))
                return Deflect(characterName);

            var lower = reply.ToLowerInvariant();
            foreach (var m in BreakMarkers)
                if (lower.Contains(m))
                    return Deflect(characterName);

            reply = Humanize(reply);
            if (string.IsNullOrWhiteSpace(reply)) return Deflect(characterName);

            if (reply.Length <= MaxChars) return reply;

            // Cut at the last sentence end before the cap; fall back to a hard cut
            // with an ellipsis if the reply is one endless sentence.
            int cut = -1;
            for (int i = Math.Min(MaxChars, reply.Length) - 1; i > 0; i--)
            {
                char c = reply[i];
                if (c == '.' || c == '!' || c == '?') { cut = i + 1; break; }
            }
            return cut > 0 ? reply.Substring(0, cut).TrimEnd() : reply.Substring(0, MaxChars).TrimEnd() + "…";
        }

        static string Deflect(string characterName) =>
            $"({characterName} looks at you a moment, seems to lose the thread, then changes the subject.)";

        /// Deterministic de-telling: fixes the mechanical "AI voice" giveaways
        /// that need no rewrite and no extra API call — dashes become commas,
        /// curly quotes go straight, markdown emphasis and emoji vanish. Word-
        /// level tells are handled upstream by the speech-style rules in the
        /// system prompt; TellCount below measures what still slips through.
        public static string Humanize(string reply)
        {
            var sb = new System.Text.StringBuilder(reply.Length);
            for (int i = 0; i < reply.Length; i++)
            {
                char c = reply[i];
                switch (c)
                {
                    case '\u2018': case '\u2019': sb.Append('\''); continue; // curly single quotes
                    case '\u201C': case '\u201D': sb.Append('"'); continue;  // curly double quotes
                    case '*': case '`': case '#': continue; // markdown artifacts
                    case '\u2014': case '\u2013':           // em/en dash → comma
                        while (sb.Length > 0 && sb[sb.Length - 1] == ' ') sb.Length--;
                        sb.Append(", ");
                        while (i + 1 < reply.Length && reply[i + 1] == ' ') i++;
                        continue;
                }
                // Emoji and dingbats (incl. all astral-plane symbols); accents survive.
                if (char.IsSurrogate(c) || (c >= '\u2600' && c <= '\u27BF') || c == '\uFE0F') continue;
                sb.Append(c);
            }
            return StripBareDecimals(sb.ToString()).Trim();
        }

        /// The legibility law's last line of defense on the game's largest
        /// text surface: a bare internal scalar ("0.62") must never reach the
        /// player, whatever the prompt fed the model (audit 2026-07-27).
        /// Money keeps its digits, days keep their dates — only unanchored
        /// decimal fractions are scrubbed.
        /// What money looks like in this city. One place, because the
        /// scrubber above and anything else that has to recognise a price
        /// must agree — and a second copy of it is how the digits went.
        public const char CurrencySymbol = '£';

        static string StripBareDecimals(string reply)
        {
            var sb = new System.Text.StringBuilder(reply.Length);
            int i = 0;
            while (i < reply.Length)
            {
                char c = reply[i];
                // THE CURRENCY SYMBOL IS A VARIABLE, not a literal. This
                // read `!= '$'`, so when the city became British every price
                // the model wrote was scrubbed down to a bare "£" — the rule
                // that exists to KEEP money's digits was deleting them,
                // because it recognised money by a symbol the game had
                // stopped using. Caught by the one test that asserted the
                // behaviour rather than the spelling.
                if (char.IsDigit(c) && (sb.Length == 0
                    || (sb[sb.Length - 1] != CurrencySymbol && !char.IsDigit(sb[sb.Length - 1]))))
                {
                    int j = i;
                    bool dot = false;
                    while (j < reply.Length && (char.IsDigit(reply[j]) || (reply[j] == '.' && !dot && j + 1 < reply.Length && char.IsDigit(reply[j + 1]))))
                    { if (reply[j] == '.') dot = true; j++; }
                    if (dot)
                    {
                        // drop the token and one adjacent space so sentences close up
                        if (sb.Length > 0 && sb[sb.Length - 1] == ' ' && j < reply.Length && reply[j] == ' ') j++;
                        i = j;
                        continue;
                    }
                }
                sb.Append(c);
                i++;
            }
            return sb.ToString();
        }

        // Written-prose words a person behind a bar would never say. Telemetry
        // only — counted, never auto-replaced (a bad swap is worse than a tell).
        static readonly string[] StyleTells =
        {
            "testament", "tapestry", "delve", "vibrant", "pivotal", "underscor",
            "showcas", "foster", "interplay", "it's not just", "it is not just",
            "not only", "crucial", "boasts",
        };

        public static int TellCount(string reply)
        {
            if (string.IsNullOrEmpty(reply)) return 0;
            var lower = reply.ToLowerInvariant();
            int n = 0;
            foreach (var t in StyleTells)
            {
                int idx = 0;
                while ((idx = lower.IndexOf(t, idx, StringComparison.Ordinal)) >= 0) { n++; idx += t.Length; }
            }
            return n;
        }
    }
}
