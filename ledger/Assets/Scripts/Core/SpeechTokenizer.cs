using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace Ledger.Core
{
    /// WORDS INTO THE NUMBERS THE MODEL READS.
    ///
    /// The last piece of the live-speech pipeline that had to be reimplemented
    /// rather than converted. The three networks are ONNX graphs; the loop and
    /// the sampler are `SpeechLoop`; this is the front door, and it could not
    /// be a graph because a vocabulary is a lookup table, not arithmetic.
    ///
    /// IT CARRIES THE SAME DANGER AS THE SAMPLER: every way of getting it
    /// slightly wrong still produces speech. A word split into the wrong
    /// pieces is perfectly pronounceable — it just comes out sounding like
    /// somebody reading a language they do not speak. There is no exception to
    /// catch and nothing to grep for.
    ///
    /// So it is checked against the real one rather than reasoned about.
    /// `tools/voice-live/tokenizer-reference.py` runs HuggingFace's own
    /// `tokenizers` over the exact vocabulary the game ships and prints the
    /// answers as C# literals; `TestSpeechTokenizer` asserts them.
    ///
    /// THE VOCABULARY, read out of the file rather than remembered: BPE, 704
    /// tokens, 265 merges, no normaliser, a `Whitespace` pre-tokeniser, no
    /// post-processor, `[UNK]` for anything missing, and `fuse_unk` false so
    /// two unknown characters stay two tokens.
    ///
    /// TWO BEHAVIOURS A REIMPLEMENTATION WOULD GET WRONG, both found by
    /// running the real thing:
    ///
    ///   `[SPACE]` IS AN ADDED TOKEN, id 2, so it is cut out of the text
    ///   before the pre-tokeniser sees it. chatterbox replaces every space
    ///   with that literal string first, so an implementation that
    ///   pre-tokenised first would split it into `[`, `SPACE`, `]` — three
    ///   wrong tokens at every word gap, in every line.
    ///
    ///   CAPITALS HAVE NO MERGES. The table was learned on lower case, so
    ///   "Hello" is H + e + ll + o rather than one piece. Not a fault to fix:
    ///   it is what the model was trained on, and `SpeechText.Normalise`
    ///   capitalises the first letter of every line, so it happens constantly.
    public sealed class SpeechTokenizer
    {
        /// HuggingFace's `Whitespace` pre-tokeniser is this regex, not a split
        /// on spaces. It separates runs of word characters from runs of
        /// punctuation, which is why "happened." becomes two pieces and
        /// "don't" becomes three.
        static readonly Regex PreToken = new Regex(@"\w+|[^\w\s]+",
            RegexOptions.Compiled | RegexOptions.CultureInvariant);

        /// What chatterbox puts in place of every space before encoding.
        public const string SpaceToken = "[SPACE]";

        readonly Dictionary<string, int> _vocab;
        readonly Dictionary<string, int> _rank;   // "a b" -> position in the merge list
        readonly List<string> _added;             // longest first
        readonly int _unk;

        SpeechTokenizer(Dictionary<string, int> vocab, Dictionary<string, int> rank,
                        List<string> added, int unk)
        {
            _vocab = vocab;
            _rank = rank;
            _added = added;
            _unk = unk;
        }

        public int Count => _vocab.Count;
        public int Merges => _rank.Count;
        public int Unknown => _unk;

        /// Read a HuggingFace `tokenizer.json`. Returns null with a reason
        /// rather than throwing, because the file is shipped data and a
        /// missing or truncated one must degrade to "this character cannot
        /// speak live" rather than to an exception crossing a frame.
        public static SpeechTokenizer Load(string json, out string why)
        {
            why = null;
            if (string.IsNullOrEmpty(json)) { why = "the vocabulary file is empty"; return null; }

            // PARSED INSIDE A CATCH, because `MiniJson.Deserialize` THROWS on
            // malformed input — "Expected string at 1" — and this class
            // promises a reason instead. The promise was in the doc comment
            // and not in the code until the test asked for it; a truncated
            // vocabulary is exactly the shape of thing that reaches a player,
            // and it must make a character quiet rather than throw across a
            // frame boundary.
            Dictionary<string, object> root;
            try
            {
                root = MiniJson.AsObject(MiniJson.Deserialize(json));
            }
            catch (Exception e)
            {
                why = "the vocabulary file will not parse: " + e.Message;
                return null;
            }
            var model = root == null ? null : MiniJson.GetObject(root, "model");
            var rawVocab = model == null ? null : MiniJson.GetObject(model, "vocab");
            var rawMerges = model == null ? null : MiniJson.GetList(model, "merges");
            if (rawVocab == null || rawMerges == null)
            {
                why = "no model.vocab / model.merges: this is not a tokenizer.json";
                return null;
            }

            var vocab = new Dictionary<string, int>(rawVocab.Count, StringComparer.Ordinal);
            foreach (var kv in rawVocab)
            {
                if (kv.Value is double d) vocab[kv.Key] = (int)d;
            }

            var rank = new Dictionary<string, int>(rawMerges.Count, StringComparer.Ordinal);
            for (int i = 0; i < rawMerges.Count; i++)
            {
                // EARLIEST WINS. A merge listed twice keeps its first rank,
                // because rank IS priority and overwriting would silently
                // reorder the table.
                if (rawMerges[i] is string s && !rank.ContainsKey(s)) rank[s] = i;
            }

            // ADDED TOKENS, LONGEST FIRST. They are matched literally against
            // the raw text before anything else touches it, and longest-first
            // is what stops a shorter one shadowing a longer one that starts
            // the same way.
            var added = new List<string>();
            var rawAdded = MiniJson.GetList(root, "added_tokens");
            if (rawAdded != null)
            {
                foreach (var a in rawAdded)
                {
                    var o = MiniJson.AsObject(a);
                    var content = o == null ? null : MiniJson.GetString(o, "content");
                    if (!string.IsNullOrEmpty(content)) added.Add(content);
                }
            }
            added.Sort((x, y) => y.Length.CompareTo(x.Length));

            string unkName = MiniJson.GetString(model, "unk_token") ?? "[UNK]";
            int unk;
            if (!vocab.TryGetValue(unkName, out unk))
            {
                why = "the vocabulary has no " + unkName + " to fall back to";
                return null;
            }
            if (vocab.Count == 0) { why = "the vocabulary is empty"; return null; }
            return new SpeechTokenizer(vocab, rank, added, unk);
        }

        /// Text to token ids, the way chatterbox does it.
        public int[] Encode(string text)
        {
            var ids = new List<int>(64);
            if (string.IsNullOrEmpty(text)) return ids.ToArray();

            // SPACES BECOME `[SPACE]` FIRST, before anything else — that is
            // `EnTokenizer.encode`, and it is why the added-token pass below
            // has anything to find.
            text = text.Replace(" ", SpaceToken);

            // Added tokens are cut out whole; whatever lies between them goes
            // through the pre-tokeniser and then BPE.
            int at = 0;
            while (at < text.Length)
            {
                int hit = -1, which = -1;
                for (int i = 0; i < _added.Count; i++)
                {
                    int p = text.IndexOf(_added[i], at, StringComparison.Ordinal);
                    if (p >= 0 && (hit < 0 || p < hit)) { hit = p; which = i; }
                }
                if (hit < 0)
                {
                    Chunk(text.Substring(at), ids);
                    break;
                }
                if (hit > at) Chunk(text.Substring(at, hit - at), ids);
                int id;
                ids.Add(_vocab.TryGetValue(_added[which], out id) ? id : _unk);
                at = hit + _added[which].Length;
            }
            return ids.ToArray();
        }

        void Chunk(string span, List<int> ids)
        {
            foreach (Match m in PreToken.Matches(span))
                Bpe(m.Value, ids);
        }

        /// One pre-token, merged down and looked up.
        void Bpe(string word, List<int> ids)
        {
            if (word.Length == 0) return;

            // Characters first — but by TEXT ELEMENT, not by char, so a
            // surrogate pair or a combining mark is not cut in half. A broken
            // pair is not in the vocabulary, so the failure would be a pair of
            // unknowns rather than an error.
            var parts = new List<string>(word.Length);
            var walker = System.Globalization.StringInfo.GetTextElementEnumerator(word);
            while (walker.MoveNext()) parts.Add((string)walker.Current);

            while (parts.Count > 1)
            {
                // The lowest-ranked adjacent pair anywhere in the word. Rank
                // IS priority: the merge table is ordered by how early the
                // pair was learned.
                int best = int.MaxValue, bestAt = -1;
                for (int i = 0; i + 1 < parts.Count; i++)
                {
                    int r;
                    if (_rank.TryGetValue(parts[i] + " " + parts[i + 1], out r) && r < best)
                    {
                        best = r;
                        bestAt = i;
                    }
                }
                if (bestAt < 0) break;

                // EVERY OCCURRENCE OF THAT PAIR, in one pass, then look again.
                // Merging only the first would let a later pair of higher rank
                // jump the queue in a repeated word.
                string a = parts[bestAt], b = parts[bestAt + 1], joined = a + b;
                var next = new List<string>(parts.Count);
                for (int i = 0; i < parts.Count; )
                {
                    if (i + 1 < parts.Count && parts[i] == a && parts[i + 1] == b)
                    {
                        next.Add(joined);
                        i += 2;
                    }
                    else
                    {
                        next.Add(parts[i]);
                        i++;
                    }
                }
                parts = next;
            }

            // `fuse_unk` is false in this vocabulary, so two unknown pieces
            // stay two unknown tokens rather than collapsing into one.
            foreach (var p in parts)
            {
                int id;
                ids.Add(_vocab.TryGetValue(p, out id) ? id : _unk);
            }
        }
    }
}
