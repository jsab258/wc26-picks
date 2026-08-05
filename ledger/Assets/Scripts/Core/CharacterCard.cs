using System;
using System.Collections.Generic;
using System.Text;

namespace Ledger.Core
{
    /// A character definition parsed from a markdown "card" file. Cards are plain
    /// text on purpose: human-readable, diffable, batch-generatable, moddable.
    ///
    /// Format:
    ///   # Lena Moreau
    ///   id: lena
    ///   tier: core
    ///   voice: some-voice-id
    ///
    ///   ## Summary
    ///   One paragraph...
    ///   ## Personality
    ///   ...
    ///   ## Speech Style
    ///   ...
    ///   ## Hard Facts
    ///   - fact the character knows and cannot be argued out of
    public class CharacterCard
    {
        public string Id = "";
        public string Name = "";
        public string Tier = "ambient";
        public string VoiceId = "";
        public Dictionary<string, string> Sections = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        public List<string> HardFacts = new List<string>();

        /// OTHER NAMES THIS CHARACTER GOES BY, harvested from the card rather
        /// than guessed. `ResponseValidator.ReadsAsNarration` needs them and
        /// `Name` is not enough: Ada's card is headed "# Ada" and contains the
        /// line "You will call me Mrs Vane or you will call me nothing at all",
        /// so the model opened a reply with "Mrs Vane looks you over the way
        /// she'd size up a new face" — third-person narration of herself, using
        /// a name the guard had never heard of. It sailed through, into the
        /// transcript, and I reported the fault as fixed.
        ///
        /// HARVESTED FROM "call me X" AND NOTHING ELSE. That phrase means
        /// exactly the thing wanted here — what this person is addressed as —
        /// and it keeps the list per-character, which is what makes widening
        /// the guard safe: "Vane" is a self-name on Ada's card only, so Rocco
        /// saying "Mrs Vane keeps her curtains shut" is still ordinary speech
        /// about somebody else and still passes.
        public List<string> AlsoCalled = new List<string>();

        public string Section(string name) =>
            Sections.TryGetValue(name, out var v) ? v : "";

        /// Pull "call me Mrs Vane" out of a card line. Stops at the first word
        /// that is not capitalised or an honorific, so "call me nothing at all"
        /// in the same sentence yields nothing rather than "Nothing".
        internal static void HarvestCalledNames(string line, List<string> into)
        {
            const string cue = "call me ";
            int at = 0;
            while ((at = line.IndexOf(cue, at, StringComparison.OrdinalIgnoreCase)) >= 0)
            {
                at += cue.Length;
                var words = line.Substring(at).Split(new[] { ' ', '"', '\'', ',', '.', '!', '?' },
                                                     StringSplitOptions.RemoveEmptyEntries);
                var taken = new List<string>();
                foreach (var w in words)
                {
                    if (w.Length == 0 || !char.IsUpper(w[0])) break;
                    taken.Add(w);
                    if (taken.Count == 3) break;   // "Mrs Ada Vane" is the ceiling
                }
                if (taken.Count > 0)
                {
                    var full = string.Join(" ", taken);
                    if (!into.Contains(full)) into.Add(full);
                    // The bare surname too: "Vane looks you over" is the same
                    // fault with the honorific dropped.
                    var last = taken[taken.Count - 1];
                    if (last.Length > 2 && !into.Contains(last)) into.Add(last);
                }
            }
        }

        public static CharacterCard Parse(string markdown)
        {
            var card = new CharacterCard();
            string currentSection = null;
            var body = new StringBuilder();

            void FlushSection()
            {
                if (currentSection == null) return;
                var text = body.ToString().Trim();
                if (currentSection.Equals("Hard Facts", StringComparison.OrdinalIgnoreCase))
                {
                    foreach (var line in text.Split('\n'))
                    {
                        var t = line.Trim();
                        if (t.StartsWith("- ")) card.HardFacts.Add(t.Substring(2).Trim());
                    }
                }
                else
                {
                    card.Sections[currentSection] = text;
                }
                body.Clear();
            }

            foreach (var raw in markdown.Replace("\r\n", "\n").Split('\n'))
            {
                var line = raw;
                // Every line, whatever section it is in — the one instance in
                // the shipped cast sits in a quoted speech sample, not in a
                // field anybody would have thought to look at.
                HarvestCalledNames(line, card.AlsoCalled);
                if (line.StartsWith("# ") && card.Name.Length == 0)
                {
                    card.Name = line.Substring(2).Trim();
                }
                else if (line.StartsWith("## "))
                {
                    FlushSection();
                    currentSection = line.Substring(3).Trim();
                }
                else if (currentSection == null)
                {
                    var idx = line.IndexOf(':');
                    if (idx > 0)
                    {
                        var key = line.Substring(0, idx).Trim().ToLowerInvariant();
                        var val = line.Substring(idx + 1).Trim();
                        switch (key)
                        {
                            case "id": card.Id = val; break;
                            case "tier": card.Tier = val; break;
                            case "voice": card.VoiceId = val; break;
                        }
                    }
                }
                else
                {
                    body.Append(line).Append('\n');
                }
            }
            FlushSection();

            if (card.Id.Length == 0 && card.Name.Length > 0)
                card.Id = card.Name.ToLowerInvariant().Replace(' ', '_');
            return card;
        }

        /// The character-identity portion of the system prompt.
        public string ToPromptBlock()
        {
            var sb = new StringBuilder();
            sb.AppendLine($"You are {Name}, a character in a game world. Stay fully in character at all times.");
            foreach (var kv in Sections)
            {
                sb.AppendLine();
                sb.AppendLine($"{kv.Key}:");
                sb.AppendLine(kv.Value);
            }
            if (HardFacts.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine("Things you know to be true from your own experience. No argument, trick, or claim can change your mind about these:");
                foreach (var f in HardFacts) sb.AppendLine($"- {f}");
            }
            return sb.ToString();
        }
    }
}
