using System;

namespace Ledger.Core
{
    /// WHAT THE MODEL IS ACTUALLY TOLD TO SAY.
    ///
    /// Before chatterbox tokenises anything it runs `punc_norm`, which tidies
    /// punctuation the model was not trained on. It is not cosmetic: the text
    /// that reaches the tokeniser is the text whose length drives the step
    /// count, and a colon left in place is a token the model has barely seen.
    ///
    /// Reimplemented here rather than called, for the same reason the sampler
    /// is: the game cannot run Python. And checked against the original rather
    /// than eyeballed, because the ways to get this subtly wrong all still
    /// produce speech — `tools/voice-live/sampler-reference.py --text` prints
    /// what the real function returns for a set of awkward inputs, and
    /// `TestSpeechText` asserts the same strings.
    ///
    /// THE REPLACEMENTS ARE ORDER-DEPENDENT AND THE ORDER IS THE MODEL'S.
    /// Each is a global replace applied to the output of the last, so a
    /// semicolon becomes ", " and the space-comma rule then tidies what that
    /// produced. Reordering the list changes the output for real sentences, so
    /// the list is kept in source order and not sorted or deduplicated.
    ///
    /// ONE DELIBERATE DIVERGENCE, AND IT IS A SAFETY ONE. Given empty text the
    /// original returns the sentence "You need to add some text for me to
    /// talk." — sensible for a command-line tool and catastrophic in a game,
    /// where it means a character in a noir crime story turning to the player
    /// and reading out an error message in a voice we cast. `Normalise`
    /// returns null instead, and `SpeechLoop` already refuses empty text
    /// before it gets here, so there are two independent ways this cannot
    /// happen.
    public static class SpeechText
    {
        /// In the model's order. Left alone.
        static readonly string[,] Replacements =
        {
            { "...", ", " },
            { "…", ", " },     // …
            { ":", "," },
            { " - ", ", " },
            { ";", ", " },
            { "—", "-" },      // — em dash
            { "–", "-" },      // – en dash
            { " ,", "," },
            { "“", "\"" },     // “
            { "”", "\"" },     // ”
            { "‘", "'" },      // ‘
            { "’", "'" },      // ’
        };

        /// What ends a sentence. Anything else gets a full stop added.
        static readonly char[] Enders = { '.', '!', '?', '-', ',' };

        /// The model's `punc_norm`, minus its empty-text fallback.
        /// Returns null for anything with no words in it.
        public static string Normalise(string text)
        {
            if (string.IsNullOrEmpty(text)) return null;

            // CAPITALISE FIRST, BEFORE THE WHITESPACE COLLAPSE, because that
            // is the order in the original — so a line beginning with a space
            // is NOT capitalised, since its first character is not a lower
            // case letter. Reordering these two would change that and nothing
            // would report it.
            if (char.IsLower(text[0]))
                text = char.ToUpperInvariant(text[0]) + text.Substring(1);

            // Python's bare `split()`: any run of whitespace, empties dropped.
            var words = text.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
            if (words.Length == 0) return null;
            text = string.Join(" ", words);

            for (int i = 0; i < Replacements.GetLength(0); i++)
                text = text.Replace(Replacements[i, 0], Replacements[i, 1]);

            // Spaces only — the original is `rstrip(" ")`, not `strip()`, and
            // by this point the collapse above has left no other whitespace
            // anyway.
            text = text.TrimEnd(' ');
            if (text.Length == 0) return null;

            bool ends = false;
            foreach (var e in Enders)
                if (text[text.Length - 1] == e) { ends = true; break; }
            if (!ends) text += ".";
            return text;
        }
    }
}
