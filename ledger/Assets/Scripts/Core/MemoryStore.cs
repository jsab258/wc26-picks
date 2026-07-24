using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Ledger.Core
{
    public class MemoryEvent
    {
        public GameTime Time;
        public string Kind;       // conversation | observation | heard | reflection
        public double Importance; // 0..1
        public string Text;

        public MemoryEvent(GameTime time, string kind, double importance, string text)
        {
            Time = time;
            Kind = kind;
            Importance = Math.Clamp(importance, 0.0, 1.0);
            Text = text.Replace("\n", " ").Trim();
        }

        public string ToLine() =>
            $"- [{Time}] ({Importance.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture)}|{Kind}) {Text}";

        public static MemoryEvent FromLine(string line)
        {
            // - [D3 14:05] (0.80|conversation) text...
            var t = line.Trim();
            if (!t.StartsWith("- [")) return null;
            int closeBracket = t.IndexOf(']');
            if (closeBracket < 0) return null;
            if (!GameTime.TryParse(t.Substring(3, closeBracket - 3), out var time)) return null;

            int openParen = t.IndexOf('(', closeBracket);
            int closeParen = t.IndexOf(')', closeBracket);
            if (openParen < 0 || closeParen < 0) return null;
            var meta = t.Substring(openParen + 1, closeParen - openParen - 1).Split('|');
            if (meta.Length != 2) return null;
            if (!double.TryParse(meta[0], System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out var importance)) return null;

            return new MemoryEvent(time, meta[1], importance, t.Substring(closeParen + 1).Trim());
        }
    }

    /// One character's persistent memory: an append-only event stream plus a small
    /// set of distilled beliefs (produced by reflection). Stored as human-readable
    /// markdown so memories can be inspected, debugged, and hand-edited.
    public class MemoryStore
    {
        public string CharacterId { get; }
        public List<string> Beliefs { get; } = new List<string>();
        public List<MemoryEvent> Events { get; } = new List<MemoryEvent>();

        readonly string _filePath; // null => in-memory only (tests)

        public MemoryStore(string characterId, string filePath = null)
        {
            CharacterId = characterId;
            _filePath = filePath;
            if (_filePath != null && File.Exists(_filePath)) LoadFrom(File.ReadAllText(_filePath));
        }

        public void Append(MemoryEvent e)
        {
            Events.Add(e);
            Save();
        }

        public void ReplaceBeliefs(IEnumerable<string> beliefs)
        {
            Beliefs.Clear();
            foreach (var b in beliefs)
            {
                var t = b.Trim().TrimStart('-', ' ');
                if (t.Length > 0) Beliefs.Add(t);
            }
            Save();
        }

        public List<MemoryEvent> EventsOnDay(int day) =>
            Events.FindAll(e => e.Time.Day == day);

        public void LoadFrom(string markdown)
        {
            Beliefs.Clear();
            Events.Clear();
            string section = null;
            foreach (var raw in markdown.Replace("\r\n", "\n").Split('\n'))
            {
                if (raw.StartsWith("## ")) { section = raw.Substring(3).Trim(); continue; }
                if (section == "Beliefs")
                {
                    var t = raw.Trim();
                    if (t.StartsWith("- ")) Beliefs.Add(t.Substring(2).Trim());
                }
                else if (section == "Events")
                {
                    var e = MemoryEvent.FromLine(raw);
                    if (e != null) Events.Add(e);
                }
            }
        }

        public string ToMarkdown()
        {
            var sb = new StringBuilder();
            sb.AppendLine($"# Memory: {CharacterId}");
            sb.AppendLine();
            sb.AppendLine("## Beliefs");
            foreach (var b in Beliefs) sb.AppendLine($"- {b}");
            sb.AppendLine();
            sb.AppendLine("## Events");
            foreach (var e in Events) sb.AppendLine(e.ToLine());
            return sb.ToString();
        }

        void Save()
        {
            if (_filePath == null) return;
            var dir = Path.GetDirectoryName(_filePath);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
            File.WriteAllText(_filePath, ToMarkdown());
        }
    }
}
