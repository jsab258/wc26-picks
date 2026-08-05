using System;
using System.Collections.Generic;

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

        /// `alsoCalled` is `CharacterCard.AlsoCalled` — the other names the card
        /// gives this person. Optional so the dozens of existing call sites that
        /// only have a name still compile and still catch the first-name case;
        /// the game passes it, because the game has the card.
        public static string Validate(string reply, string characterName,
                                      IReadOnlyList<string> alsoCalled = null)
        {
            if (string.IsNullOrWhiteSpace(reply))
                return Deflect(characterName);

            var lower = reply.ToLowerInvariant();
            foreach (var m in BreakMarkers)
                if (lower.Contains(m))
                    return Deflect(characterName);

            reply = Humanize(reply);
            if (string.IsNullOrWhiteSpace(reply)) return Deflect(characterName);

            // NARRATION IS NOT SPEECH, and this is from a real transcript.
            // Asked something he could not answer, one character replied
            // "Sam squints at that like you've asked him to fly" — prose ABOUT
            // a person rather than a person talking. The prompt now forbids it,
            // and a prompt rule with nothing behind it is a suggestion: this is
            // the only reply in the game nobody wrote and nobody reviews.
            //
            // Detected by the character narrating THEMSELVES in the third
            // person, which is what the failure looks like and is cheap to
            // spot. Deliberately narrow — a character may legitimately talk
            // about somebody else in the third person all day, and about
            // themselves by name when quoting what others call them. Only a
            // reply that OPENS with their own name and a verb is the shape
            // that went wrong.
            if (ReadsAsNarration(reply, characterName, alsoCalled)) return Deflect(characterName);

            // LAYER 2 — SHAPE, on the one text in this game that nobody wrote
            // and nobody reviewed.
            //
            // `Humanize` handles the AI tells: em-dashes, curly quotes,
            // markdown, emoji. It has no opinion about form, and a model reply
            // arrives with all of it — a double space, a space before a comma,
            // a sentence that lost its capital, "to the the warehouse", a
            // quote it ran out of tokens before closing. Those are mechanical,
            // so `Tidy` repairs them rather than throwing the reply away: a
            // character standing there losing the thread because a space was
            // wrong would be a worse bug than the space.
            //
            // WHAT SURVIVES REPAIR IS A BROKEN REPLY. After `Tidy` the only
            // faults left are an unresolved `{placeholder}` and punctuation
            // that makes no sense — both mean the reply is not a line of
            // dialogue, and the in-character deflection is exactly right for
            // that. This is also the call site the reach check demanded:
            // `TextShape` shipped as a checker with no caller in the game,
            // which is the failure mode the checker exists to catch.
            reply = TextShape.Tidy(reply);
            if (!TextShape.IsWellFormed(reply)) return Deflect(characterName);

            if (reply.Length <= MaxChars) return reply;

            // Cut at the last sentence end before the cap; fall back to a hard cut
            // with an ellipsis if the reply is one endless sentence.
            int cut = -1;
            for (int i = Math.Min(MaxChars, reply.Length) - 1; i > 0; i--)
            {
                char c = reply[i];
                if (c == '.' || c == '!' || c == '?') { cut = i + 1; break; }
            }
            // THE ELLIPSIS HAS TO FIT INSIDE THE CAP, NOT AFTER IT. The hard-cut
            // branch took `MaxChars` characters and then appended a character,
            // so the one thing `MaxChars` promises — that nothing longer than
            // this reaches the screen — was false by exactly one for every
            // endless sentence a model ever produced. `Adversary` measured it:
            // thirty replies over the bound, worst case 901.
            //
            // One character is not a crisis and the constant is PUBLIC, which
            // is what makes it worth fixing rather than rounding off: anything
            // sizing a caption box or a buffer from `MaxChars` is sized one
            // short, and the failure would land in the UI, far from here.
            return cut > 0
                ? reply.Substring(0, cut).TrimEnd()
                : reply.Substring(0, MaxChars - 1).TrimEnd() + "…";
        }

        static string Deflect(string characterName) =>
            $"({characterName} looks at you a moment, seems to lose the thread, then changes the subject.)";

        /// Deterministic de-telling: fixes the mechanical "AI voice" giveaways
        /// that need no rewrite and no extra API call — dashes become commas,
        /// curly quotes go straight, markdown emphasis and emoji vanish. Word-
        /// level tells are handled upstream by the speech-style rules in the
        /// system prompt; TellCount below measures what still slips through.
        /// Does this reply read as stage direction rather than speech?
        ///
        /// NARROW ON PURPOSE. The observed failure opens with the speaker's own
        /// name followed by a verb — "Sam squints...", "Rocco laughs...". A
        /// broader test would catch a character talking about a third party,
        /// which is most of what anybody says in this game, and deflecting
        /// those would be far worse than the fault it fixes.
        ///
        /// AND "THE SPEAKER'S OWN NAME" WAS THE WRONG HALF TO BE NARROW ABOUT.
        /// This tested `characterName.Split(' ')[0]` and nothing else, so it
        /// caught the three cases in the transcript it was written from and
        /// missed the next one entirely: Ada's card is headed "# Ada" and says
        /// "You will call me Mrs Vane", and the model wrote "Mrs Vane looks you
        /// over the way she'd size up a new face at the back of a classroom."
        /// Same fault, same shape, a name the guard did not hold.
        ///
        /// So the SHAPE stays exactly as narrow as it was — own name, then a
        /// lowercase verb — and the NAME SET grows to every name the card gives
        /// this character: all tokens of `Name`, plus `CharacterCard.AlsoCalled`.
        /// That set is per-character, which is what keeps the third-party case
        /// safe: "Vane" is a self-name on Ada's card only, so Rocco saying
        /// "Vane keeps her curtains shut" is still speech and still passes.
        public static bool ReadsAsNarration(string reply, string characterName,
                                            IReadOnlyList<string> alsoCalled = null)
        {
            if (string.IsNullOrWhiteSpace(reply) || string.IsNullOrWhiteSpace(characterName))
                return false;

            var t = reply.TrimStart();
            // LONGEST FIRST, so "Mrs Vane looks" is tested against "Mrs Vane"
            // before "Vane" — otherwise the short match leaves "Vane looks" as
            // the remainder and the next character read is 'V', not a verb.
            var names = new List<string>();
            foreach (var tok in characterName.Split(' '))
                if (tok.Length > 2) names.Add(tok);
            if (alsoCalled != null)
                foreach (var n in alsoCalled)
                    if (!string.IsNullOrWhiteSpace(n)) names.Add(n.Trim());
            names.Sort((a, b) => b.Length.CompareTo(a.Length));

            foreach (var name in names)
            {
                if (!t.StartsWith(name, StringComparison.OrdinalIgnoreCase)) continue;
                var rest = t.Substring(name.Length);
                // The name must END here: "Sammy grins" is not Sam narrating.
                if (rest.Length > 0 && (char.IsLetterOrDigit(rest[0]) || rest[0] == '\'')) continue;
                rest = rest.TrimStart();
                // A quote or a comma after the name is somebody being addressed
                // or quoted, not narrated. A bare word after it is a verb.
                if (rest.Length == 0) continue;
                char c = rest[0];
                if (c == ',' || c == '?' || c == '!' || c == '.' || c == ':' || c == '"') continue;
                int end = rest.IndexOf(' ');
                var word = end < 0 ? rest : rest.Substring(0, end);
                // Lowercase word straight after the speaker's own name: "Sam
                // squints", "Ada considers". Capitalised would be another name.
                if (word.Length > 2 && char.IsLower(word[0])) return true;
            }
            return false;
        }

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
