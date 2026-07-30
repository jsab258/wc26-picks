using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// WHICH RECORDING IS THIS LINE — audit items 5 and 7, which turn out to
    /// be the same question.
    ///
    /// Item 7 said there was no voice bus. There is one now, and it needs to
    /// be handed a filename. Item 5 said nothing specified determinism: a
    /// cloner given the same reference and the same text can produce a
    /// different take, so if the bank is ever regenerated every character
    /// drifts. Both are answered by one rule:
    ///
    ///   **A clip is named by a hash of who is speaking and what they say,
    ///   and the generator seeds itself from the same hash.**
    ///
    /// So the game can ask for a line by computing the name, the generator
    /// can produce it by computing the same name, neither has to consult a
    /// manifest, and regenerating the bank next month yields byte-identical
    /// takes rather than nineteen people who now sound slightly different.
    ///
    /// THE HASH IS WRITTEN OUT BY HAND ON PURPOSE. `string.GetHashCode()` is
    /// randomised per process in modern .NET; it is stable in Unity's runtime
    /// today and that is an accident of the runtime, not a promise. A cache
    /// key that changes when the engine updates would silently orphan the
    /// entire bank, and the failure would look like every voice vanishing at
    /// once for no reason anybody could trace. FNV-1a is nine lines and it is
    /// the same number on every platform, in every process, forever.
    public static class VoiceBank
    {
        /// The background voices the crowd draws from — and these are not a
        /// number I picked, they are the six crowd entries the casting sheet
        /// actually funds (`tools/voice-fetch`, tier "crowd").
        ///
        /// SIX IS THIN and it is written down here rather than papered over.
        /// The ear picks out a repeated voice on a busy street inside a
        /// minute, and a city where every seventh person shares a throat
        /// reads worse than one with no voices at all. The fix is more crowd
        /// entries in the casting sheet, which costs generation time — not a
        /// larger constant here, which would only name files nobody is ever
        /// going to produce and turn a thin bank into a silent one.
        public static readonly string[] PoolMasculine = { "crowd_m1", "crowd_m2", "crowd_m3" };
        public static readonly string[] PoolFeminine = { "crowd_f1", "crowd_f2", "crowd_f3" };

        public static int PoolVoices => PoolMasculine.Length + PoolFeminine.Length;

        /// The named voices, copied from the casting sheet the fetcher works
        /// from (`tools/voice-fetch`, tiers "principal" and "street").
        ///
        /// AND THESE DO NOT ALL MATCH THE ROSTER. The game's gossipers use
        /// ids like `sera`, `aldous`, `danny`, `halvard`, `june`, `zlata`;
        /// the casting sheet has `kest`, `vesna`, `marla`. Some are the same
        /// person under two names and some are people nobody has cast. The
        /// consequence is contained and deliberate — an id not in this set
        /// draws a crowd voice rather than throwing — but it means a named
        /// character can quietly end up sounding like a passer-by, so the
        /// reconciliation is a casting task somebody has to actually do.
        public static readonly HashSet<string> Cast = new HashSet<string>
        {
            "lena", "rocco", "ellis", "reese", "kest",
            "sam", "ada", "vesna", "marla", "joey", "rita", "hal", "emil",
        };

        /// The byte between the voice and the words when they are hashed.
        ///
        /// NOT AN EMPTY STRING. Concatenating with nothing between them makes
        /// ("ab","cd") and ("abc","d") hash identically — harmless for the
        /// filename, where the voice is also the folder, and not harmless for
        /// `Seed`, where two different lines would then generate as the same
        /// take. A unit separator, because it cannot occur in a line of
        /// dialogue, written as an escape because a raw control byte sitting
        /// in a source file is a thing nobody should have to discover.
        const string Sep = "\u001f";

        /// FNV-1a, 32-bit. Stable across platforms, processes and runtimes.
        public static uint Hash(string s)
        {
            unchecked
            {
                uint h = 2166136261u;
                if (s == null) return h;
                for (int i = 0; i < s.Length; i++)
                {
                    h ^= s[i];
                    h *= 16777619u;
                }
                return h;
            }
        }

        /// What the hash is actually taken over.
        ///
        /// Whitespace is collapsed because a line that gained a double space
        /// in an edit is the same line and must not orphan its recording.
        /// CASE IS KEPT: capitals change how a text-to-speech engine reads a
        /// sentence — emphasis, initialisms, the difference between "no" and
        /// "NO" — so two lines differing only in case are two different
        /// performances and deserve two different files.
        public static string Normalise(string text)
        {
            if (string.IsNullOrEmpty(text)) return "";
            var sb = new System.Text.StringBuilder(text.Length);
            bool space = false;
            foreach (var ch in text)
            {
                if (char.IsWhiteSpace(ch)) { space = sb.Length > 0; continue; }
                if (space) { sb.Append(' '); space = false; }
                sb.Append(ch);
            }
            return sb.ToString();
        }

        /// The clip's name: `voice/hash`, and nothing else.
        ///
        /// No slot id, no line index, no scene, no act. Every one of those is
        /// a thing that can be renamed while the words stay identical, and a
        /// filename that changes when the words did not is how a bank rots.
        /// Returns null for anything unspeakable, so a caller cannot get a
        /// plausible-looking path for a line that does not exist.
        public static string ClipName(string voiceId, string text)
        {
            var t = Normalise(text);
            if (string.IsNullOrEmpty(voiceId) || t.Length == 0) return null;
            return voiceId + "/" + Hash(voiceId + Sep + t).ToString("x8");
        }

        /// The generator's random seed for that clip.
        ///
        /// Same inputs, same seed, same take — which is the whole of audit
        /// item 5. Non-negative because every RNG this project uses takes an
        /// `int` and half of them treat a negative as an error.
        public static int Seed(string voiceId, string text)
        {
            var t = Normalise(text);
            if (string.IsNullOrEmpty(voiceId) || t.Length == 0) return 0;
            return (int)(Hash(voiceId + Sep + t) & 0x7fffffff);
        }

        /// Which voice a given speaker uses.
        ///
        /// A cast member IS their voice — Rocco is cast, recorded and named.
        /// Everybody else draws from the crowd pool, deterministically by id,
        /// so the same walker sounds like the same person every time you pass
        /// them and nobody has to store which voice they got.
        ///
        /// `masculine` is null when the caller does not know, and today every
        /// caller is null: `SpeechBubble` gets a Transform, not a resident
        /// record, so the speaker's gender is not in reach at the point the
        /// line is spoken. Said out loud rather than defaulted quietly —
        /// unknown means the pool is drawn from as a whole, which will
        /// sometimes put a woman's voice on a man until the population record
        /// is threaded through to the call site.
        public static string VoiceFor(string speakerId, ICollection<string> castVoiceIds,
                                      bool? masculine = null)
        {
            if (string.IsNullOrEmpty(speakerId)) return null;
            if (castVoiceIds != null && castVoiceIds.Contains(speakerId)) return speakerId;
            uint h = Hash(speakerId);
            if (masculine == true) return PoolMasculine[h % (uint)PoolMasculine.Length];
            if (masculine == false) return PoolFeminine[h % (uint)PoolFeminine.Length];
            return (h % 2 == 0 ? PoolMasculine : PoolFeminine)
                   [(h / 2) % (uint)PoolMasculine.Length];
        }

        /// A stable seed for anything else that needs to vary by line and
        /// must not vary by run — the word-dropping in `Acoustics.AsHeard`
        /// being the one that already existed and was reaching for
        /// `string.GetHashCode()` to get it.
        public static int SeedFor(string text) => (int)(Hash(Normalise(text)) & 0x7fffffff);
    }
}
