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

        public string Section(string name) =>
            Sections.TryGetValue(name, out var v) ? v : "";

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
