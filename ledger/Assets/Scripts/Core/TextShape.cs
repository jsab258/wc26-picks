using System;
using System.Collections.Generic;
using System.Text;

namespace Ledger.Core
{
    /// LAYER 2 — SHAPE. Is the line well-formed, whatever it says.
    ///
    /// WHY THIS EXISTS. Twenty-one of the forty-two gossip templates in
    /// `StreetVoice` rendered a sentence beginning with a lowercase letter —
    /// *"the new owner was at the warehouse on Tuesday."* — and did so for
    /// weeks, under 2,883 passing tests. Every one of those tests asserted
    /// what the line MEANT: that it named the right person, carried the right
    /// rumour, differed by confidence band. Not one of them looked at it.
    ///
    /// That is a whole class of defect, not a slip. A test written by the
    /// person who wrote the feature asks the questions that person was already
    /// thinking about, and nobody thinking about a belief network is thinking
    /// about capital letters. The fix is not more care; it is a check that
    /// knows nothing about meaning and everything about form, applied to every
    /// line the game can produce.
    ///
    /// DELIBERATELY MECHANICAL. Nothing here has an opinion about writing.
    /// It cannot tell you a line is limp, and it is not supposed to — a shape
    /// check that starts making style judgements starts producing findings
    /// somebody has to argue with, and a check people argue with gets turned
    /// off. Every rule below is one where the answer is not a matter of taste.
    ///
    /// Engine-free and allocation-light: this runs over 2,604 authored bark
    /// lines and every template render in CoreTests.
    public static class TextShape
    {
        /// Titles and abbreviations that end in a full stop WITHOUT ending the
        /// sentence. Without these, "Ask Mr. Novak." is a capitalisation fault
        /// and the check is wrong about the one thing it is for.
        static readonly string[] NotASentenceEnd =
        {
            "Mr", "Mrs", "Ms", "Dr", "St", "Sgt", "Insp", "Rev", "Prof",
            "no", "No", "vs", "etc", "approx", "Ave", "Rd",
        };

        /// A fault, named so a failure message says which rule and where.
        public struct Fault
        {
            public string Rule;
            public int At;
            public string Detail;
            public override string ToString() => $"{Rule}@{At}: {Detail}";
        }

        /// Every way this line is malformed. Empty list means well-formed.
        ///
        /// `allowLowerStart` is for fragments that are legitimately not
        /// sentences — a UI chip reading "not now", a list item. It has to be
        /// asked for explicitly, because the default being strict is the whole
        /// point: the capitalisation bug survived precisely because nothing
        /// had an opinion by default.
        public static List<Fault> Faults(string line, bool allowLowerStart = false)
        {
            var faults = new List<Fault>();
            void Bad(string rule, int at, string detail) =>
                faults.Add(new Fault { Rule = rule, At = at, Detail = detail });

            if (line == null) { Bad("null", 0, "line is null"); return faults; }
            if (line.Length == 0) { Bad("empty", 0, "line is empty"); return faults; }
            if (line.Trim().Length == 0) { Bad("blank", 0, "line is only whitespace"); return faults; }

            if (line != line.Trim())
                Bad("edge-space", 0, "leading or trailing whitespace");

            // AN UNRESOLVED PLACEHOLDER IS THE LOUDEST POSSIBLE BUG and the
            // cheapest to catch: `{who} was at the warehouse` shipped to a
            // player is the game admitting it is a template.
            int open = line.IndexOf('{');
            if (open >= 0 && line.IndexOf('}', open) > open)
                Bad("placeholder", open,
                    line.Substring(open, Math.Min(24, line.Length - open)));

            for (int i = 1; i < line.Length; i++)
            {
                if (line[i] == ' ' && line[i - 1] == ' ')
                { Bad("double-space", i, "two spaces"); break; }
            }

            // Space before punctuation that closes: " ," and " ." are the
            // signature of a template whose slot rendered empty.
            for (int i = 1; i < line.Length; i++)
            {
                if (line[i - 1] != ' ') continue;
                char c = line[i];
                if (c == ',' || c == '.' || c == '!' || c == '?' || c == ';'
                    || c == ':' || c == ')' || c == '\'' && i + 1 < line.Length && line[i + 1] == 's')
                { Bad("space-before", i, $"space before '{c}'"); break; }
            }

            // Doubled punctuation, with `...` and `?!` exempt because both are
            // things a person writes on purpose.
            for (int i = 1; i < line.Length; i++)
            {
                char a = line[i - 1], b = line[i];
                if (a != b) continue;
                if (a == '.' ) continue;            // ellipsis, handled below
                if (a == ',' || a == '!' || a == '?' || a == ';' || a == ':' || a == '-')
                { Bad("doubled-punct", i, $"'{a}{b}'"); break; }
            }
            // Two full stops is a typo; three is an ellipsis; four is a typo.
            for (int i = 0; i < line.Length; i++)
            {
                if (line[i] != '.') continue;
                int run = 0;
                while (i + run < line.Length && line[i + run] == '.') run++;
                if (run == 2 || run > 3)
                { Bad("doubled-punct", i, new string('.', run)); break; }
                i += run - 1;
            }

            // A comma or full stop with nothing before it.
            //
            // EXCEPT A LEADING ELLIPSIS, which is somebody trailing off or not
            // answering — "..." and "...Evening." are two of the lines in
            // `recognition.avoids`, and they are the correct content for a
            // person who would rather you were not talking to them. First run
            // of this check flagged both, which is the instrument being wrong
            // about the subject rather than the other way round.
            string t = line.TrimStart();
            char first = t[0];
            bool leadingEllipsis = t.StartsWith("...", StringComparison.Ordinal);
            if (!leadingEllipsis && (first == ',' || first == '.' || first == ';'
                                     || first == ':' || first == '!' || first == '?'))
                Bad("orphan-punct", 0, $"line opens with '{first}'");

            // Balanced pairs. Apostrophes are excluded on purpose — "'ere"
            // and "Novak's" both make an odd count and both are correct.
            int paren = 0, square = 0;
            foreach (char c in line)
            {
                if (c == '(') paren++;
                else if (c == ')') paren--;
                else if (c == '[') square++;
                else if (c == ']') square--;
                if (paren < 0 || square < 0) break;
            }
            if (paren != 0) Bad("unbalanced", 0, "parentheses");
            if (square != 0) Bad("unbalanced", 0, "brackets");
            int dq = 0;
            foreach (char c in line) if (c == '"') dq++;
            if (dq % 2 != 0) Bad("unbalanced", 0, "double quotes");

            // THE ONE THIS FILE EXISTS FOR. The first letter of the line, and
            // the first letter after every sentence end.
            if (!allowLowerStart)
            {
                for (int i = 0; i < line.Length; i++)
                {
                    if (!char.IsLetter(line[i])) continue;
                    if (char.IsLower(line[i]))
                        Bad("lower-start", i, Excerpt(line, 0));
                    break;
                }
            }

            for (int i = 0; i < line.Length - 1; i++)
            {
                if (line[i] != '.' && line[i] != '!' && line[i] != '?') continue;
                // Skip to the next letter, over the space and any quote mark.
                int j = i + 1;
                if (line[i] == '.' && j < line.Length && line[j] == '.')
                {
                    while (j < line.Length && line[j] == '.') j++;   // ellipsis
                    // "...and then" is a legitimate continuation, not a new
                    // sentence. Only a full stop that stands alone starts one.
                    i = j - 1;
                    continue;
                }
                if (j >= line.Length || line[j] != ' ') continue;
                if (line[i] == '.' && EndsWithAbbreviation(line, i)) continue;
                while (j < line.Length && (line[j] == ' ' || line[j] == '"'
                                           || line[j] == '\'' || line[j] == '('))
                    j++;
                if (j < line.Length && char.IsLower(line[j]))
                    Bad("lower-sentence", j, Excerpt(line, i));
            }

            var doubled = DoubledWord(line);
            if (doubled != null) Bad("doubled-word", 0, doubled);

            return faults;
        }

        /// True when the line is well-formed. The common call.
        public static bool IsWellFormed(string line, bool allowLowerStart = false) =>
            Faults(line, allowLowerStart).Count == 0;

        /// Repair what is mechanically repairable, and change nothing else.
        ///
        /// This exists for the LLM path. A model reply is the one text in the
        /// game nobody wrote and nobody reviewed, and it arrives with exactly
        /// the faults above: a double space, a space before a comma, a
        /// sentence that forgot its capital, "the the". Rejecting a reply over
        /// a double space would be absurd — the character would stand there
        /// losing the thread because a space was wrong. So: fix the mechanical
        /// ones here, and let `Validate` deflect only on what survives, which
        /// is the class that means the reply is genuinely broken.
        ///
        /// NOTHING HERE TOUCHES MEANING. No word is added, removed or replaced
        /// except a duplicate of the one before it.
        public static string Tidy(string line)
        {
            if (string.IsNullOrEmpty(line)) return line;
            var sb = new StringBuilder(line.Length);

            // Collapse runs of whitespace, and drop a space that sits in front
            // of punctuation which closes.
            for (int i = 0; i < line.Length; i++)
            {
                char c = line[i];
                if (c == ' ' || c == '\t')
                {
                    if (sb.Length == 0) continue;
                    if (sb[sb.Length - 1] == ' ') continue;
                    int j = i;
                    while (j < line.Length && (line[j] == ' ' || line[j] == '\t')) j++;
                    if (j < line.Length && ",.!?;:)".IndexOf(line[j]) >= 0) { continue; }
                    sb.Append(' ');
                    continue;
                }
                sb.Append(c);
            }

            // An unmatched double quote at the end of a reply is a model
            // running out of tokens mid-clause. Dropping the orphan is kinder
            // than deflecting the whole line over it.
            int dq = 0;
            for (int i = 0; i < sb.Length; i++) if (sb[i] == '"') dq++;
            if (dq % 2 != 0)
                for (int i = sb.Length - 1; i >= 0; i--)
                    if (sb[i] == '"') { sb.Remove(i, 1); break; }

            var s = sb.ToString().Trim();
            if (s.Length == 0) return s;

            // Capitalise the first letter, and the first letter of every
            // sentence after it. Uses the same abbreviation table as the
            // check, so `Tidy` and `Faults` cannot disagree about where a
            // sentence ends.
            var chars = s.ToCharArray();
            for (int i = 0; i < chars.Length; i++)
            {
                if (!char.IsLetter(chars[i])) continue;
                chars[i] = char.ToUpperInvariant(chars[i]);
                break;
            }
            for (int i = 0; i < chars.Length - 1; i++)
            {
                if (chars[i] != '.' && chars[i] != '!' && chars[i] != '?') continue;
                int j = i + 1;
                if (chars[i] == '.' && j < chars.Length && chars[j] == '.')
                {
                    while (j < chars.Length && chars[j] == '.') j++;
                    i = j - 1;
                    continue;
                }
                if (j >= chars.Length || chars[j] != ' ') continue;
                if (chars[i] == '.' && EndsWithAbbreviation(s, i)) continue;
                while (j < chars.Length && (chars[j] == ' ' || chars[j] == '"'
                                            || chars[j] == '\'' || chars[j] == '('))
                    j++;
                if (j < chars.Length) chars[j] = char.ToUpperInvariant(chars[j]);
            }
            s = new string(chars);

            // "to the the warehouse" — drop the second one.
            //
            // Word-level, deliberately. The first attempt did index arithmetic
            // on the string returned by `DoubledWord` and was unreadable
            // enough that I could not convince myself it terminated, which is
            // its own kind of bug in a function that runs on every reply the
            // player reads.
            return string.Join(" ", DropDoubledWords(s.Split(' ')));
        }

        /// One string naming every fault, for a test failure message that
        /// says what is wrong rather than that something is.
        public static string Describe(string line, bool allowLowerStart = false)
        {
            var f = Faults(line, allowLowerStart);
            if (f.Count == 0) return "";
            var sb = new StringBuilder();
            for (int i = 0; i < f.Count; i++)
            {
                if (i > 0) sb.Append("; ");
                sb.Append(f[i].ToString());
            }
            return sb.ToString();
        }

        /// Consecutive identical tokens, where the token is one of the small
        /// words a bad join duplicates. Compared on letters only, so "the"
        /// and "the," are the same word and "The the" is caught.
        static List<string> DropDoubledWords(string[] words)
        {
            var kept = new List<string>(words.Length);
            foreach (var w in words)
            {
                if (kept.Count > 0)
                {
                    string a = Letters(kept[kept.Count - 1]);
                    string b = Letters(w);
                    if (a.Length > 0 && string.Equals(a, b, StringComparison.OrdinalIgnoreCase)
                        && IsJoinWord(a))
                    {
                        // Keep whichever carries the punctuation, so
                        // "the the." does not become "the" and lose the stop.
                        if (w.Length > a.Length) kept[kept.Count - 1] = w;
                        continue;
                    }
                }
                kept.Add(w);
            }
            return kept;
        }

        static string Letters(string w)
        {
            var sb = new StringBuilder(w.Length);
            foreach (char c in w) if (char.IsLetter(c)) sb.Append(c);
            return sb.ToString();
        }

        static bool IsJoinWord(string w)
        {
            foreach (var j in new[] { "the", "a", "to", "of", "and", "in", "at", "is" })
                if (string.Equals(w, j, StringComparison.OrdinalIgnoreCase)) return true;
            return false;
        }

        static bool EndsWithAbbreviation(string line, int dot)
        {
            int start = dot;
            while (start > 0 && char.IsLetter(line[start - 1])) start--;
            string word = line.Substring(start, dot - start);
            if (word.Length == 1) return true;           // an initial: "J. Novak"
            foreach (var a in NotASentenceEnd)
                if (string.Equals(word, a, StringComparison.Ordinal)) return true;
            return false;
        }

        /// "the the warehouse". Cheap, and it is the one repeated-word class a
        /// template concatenation actually produces.
        static string DoubledWord(string line)
        {
            string prev = null;
            int i = 0;
            while (i < line.Length)
            {
                while (i < line.Length && !char.IsLetter(line[i])) i++;
                int s = i;
                while (i < line.Length && (char.IsLetter(line[i]) || line[i] == '\'')) i++;
                if (i == s) break;
                string w = line.Substring(s, i - s);
                // "had had" and "that that" are real English; the ones that
                // matter are the articles and prepositions a join duplicates,
                // and the list lives in one place so the detector and `Tidy`
                // cannot drift apart about what counts.
                if (prev != null && w.Length > 1
                    && string.Equals(w, prev, StringComparison.OrdinalIgnoreCase)
                    && IsJoinWord(w))
                    return $"'{prev} {w}'";
                prev = w;
            }
            return null;
        }

        static string Excerpt(string line, int at)
        {
            int s = Math.Max(0, at - 4);
            int len = Math.Min(34, line.Length - s);
            return line.Substring(s, len);
        }
    }
}
