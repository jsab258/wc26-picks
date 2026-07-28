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
            if (openParen < 0) return null;
            // Search for the closing paren AFTER the opening one. A ')' that appears
            // earlier (e.g. a hand-edited ":)" before the metadata) must not be picked
            // up, or the Substring length goes negative and throws — aborting the whole
            // memory load over one malformed line. Return null instead: skip the line.
            int closeParen = t.IndexOf(')', openParen);
            if (closeParen < 0) return null;
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
        /// A long campaign must not grow a brain without bound (audit
        /// 2026-07-27): past this cap the weakest events from the OLDER half
        /// give way in blocks, so the day that mattered survives a thousand
        /// ordinary hours. Generous on purpose — pruning is for scale, not
        /// for forgetting.
        public const int MaxEvents = 600;
        const int PruneTo = 500;

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
            if (Events.Count > MaxEvents)
            {
                Prune();
                Save();          // structure changed: full rewrite
            }
            else if (!AppendToFile(e)) Save();
        }

        /// Drop the lowest-importance events from the older half until the
        /// list is back to PruneTo. Recency shields the newer half entirely.
        void Prune()
        {
            int half = Events.Count / 2;
            var oldHalf = Events.GetRange(0, half);
            oldHalf.Sort((x, y) => x.Importance.CompareTo(y.Importance));
            int toDrop = Events.Count - PruneTo;
            var doomed = new HashSet<MemoryEvent>(oldHalf.GetRange(0, Math.Min(toDrop, oldHalf.Count)));
            Events.RemoveAll(doomed.Contains);
        }

        /// Events are the file's last section, so a new one can ride an O(1)
        /// file append instead of rewriting the whole markdown — the rewrite
        /// made every remembered hour cost all the hours before it (audit
        /// 2026-07-27). Returns false when a full save is needed instead.
        bool AppendToFile(MemoryEvent e)
        {
            if (_filePath == null) return true;      // in-memory store: nothing to write
            if (!File.Exists(_filePath)) return false;
            try { File.AppendAllText(_filePath, e.ToLine() + "\n"); return true; }
            catch { return false; }
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
