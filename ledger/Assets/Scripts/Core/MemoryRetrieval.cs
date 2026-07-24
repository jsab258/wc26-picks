using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Relevance x recency x importance retrieval over a memory stream —
    /// the Stanford generative-agents pattern, with cheap keyword relevance
    /// for M0 (embeddings can replace the relevance term later without
    /// changing callers).
    public static class MemoryRetrieval
    {
        static readonly HashSet<string> Stopwords = new HashSet<string>
        {
            "the","a","an","and","or","but","of","to","in","on","at","is","are","was","were",
            "i","you","he","she","it","we","they","me","him","her","them","my","your","his",
            "its","our","their","this","that","these","those","be","been","do","did","have",
            "has","had","not","no","yes","so","if","then","than","as","for","with","about",
            "what","who","when","where","why","how","said","says","say"
        };

        public static List<string> Tokenize(string text)
        {
            var tokens = new List<string>();
            var current = new System.Text.StringBuilder();
            foreach (var c in text.ToLowerInvariant())
            {
                if (char.IsLetterOrDigit(c)) current.Append(c);
                else
                {
                    if (current.Length > 1 && !Stopwords.Contains(current.ToString()))
                        tokens.Add(current.ToString());
                    current.Clear();
                }
            }
            if (current.Length > 1 && !Stopwords.Contains(current.ToString()))
                tokens.Add(current.ToString());
            return tokens;
        }

        public static double Score(MemoryEvent e, HashSet<string> queryTokens, GameTime now,
            double wRecency = 1.0, double wImportance = 1.0, double wRelevance = 1.5)
        {
            double hoursAgo = Math.Max(0, (now.TotalMinutes - e.Time.TotalMinutes) / 60.0);
            double recency = Math.Exp(-hoursAgo / 48.0); // half-ish life about two game days

            double relevance = 0;
            if (queryTokens.Count > 0)
            {
                var eventTokens = Tokenize(e.Text);
                if (eventTokens.Count > 0)
                {
                    int overlap = eventTokens.Count(queryTokens.Contains);
                    relevance = (double)overlap / Math.Sqrt(eventTokens.Count);
                }
            }

            return wRecency * recency + wImportance * e.Importance + wRelevance * relevance;
        }

        public static List<MemoryEvent> Retrieve(MemoryStore store, string query, GameTime now, int topK = 8)
        {
            var queryTokens = new HashSet<string>(Tokenize(query ?? ""));
            return store.Events
                .OrderByDescending(e => Score(e, queryTokens, now))
                .Take(topK)
                .OrderBy(e => e.Time.TotalMinutes) // present chronologically to the model
                .ToList();
        }
    }
}
