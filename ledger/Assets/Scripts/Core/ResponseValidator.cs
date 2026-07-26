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
    }
}
