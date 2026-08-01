using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Ledger.Core
{
    /// Minimal dependency-free JSON reader/writer for the Anthropic API wire format.
    /// Deliberately tiny: objects -> Dictionary&lt;string, object&gt;, arrays -> List&lt;object&gt;,
    /// numbers -> double, plus string/bool/null. Avoids external packages so the same
    /// code runs under Unity (Mono/IL2CPP) and plain .NET without special setup.
    public static class MiniJson
    {
        public static string EscapeString(string s)
        {
            var sb = new StringBuilder(s.Length + 8);
            foreach (var c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            return sb.ToString();
        }

        public static string Serialize(object value)
        {
            var sb = new StringBuilder();
            Write(sb, value);
            return sb.ToString();
        }

        static void Write(StringBuilder sb, object value)
        {
            switch (value)
            {
                case null: sb.Append("null"); break;
                case bool b: sb.Append(b ? "true" : "false"); break;
                case string s: sb.Append('"').Append(EscapeString(s)).Append('"'); break;
                case int i: sb.Append(i.ToString(CultureInfo.InvariantCulture)); break;
                case long l: sb.Append(l.ToString(CultureInfo.InvariantCulture)); break;
                case double d: sb.Append(d.ToString("R", CultureInfo.InvariantCulture)); break;
                case IDictionary<string, object> dict:
                    sb.Append('{');
                    var firstKey = true;
                    foreach (var kv in dict)
                    {
                        if (!firstKey) sb.Append(',');
                        firstKey = false;
                        sb.Append('"').Append(EscapeString(kv.Key)).Append("\":");
                        Write(sb, kv.Value);
                    }
                    sb.Append('}');
                    break;
                case IEnumerable<object> list:
                    sb.Append('[');
                    var firstItem = true;
                    foreach (var item in list)
                    {
                        if (!firstItem) sb.Append(',');
                        firstItem = false;
                        Write(sb, item);
                    }
                    sb.Append(']');
                    break;
                default:
                    throw new ArgumentException($"MiniJson cannot serialize type {value.GetType()}");
            }
        }

        // Hostile or corrupt input can nest objects/arrays arbitrarily deep. Since the
        // parser recurses, that means a StackOverflowException — which .NET cannot catch,
        // so it takes the whole process down (a crash from a single bad API frame). Cap
        // the depth and throw a normal, catchable FormatException instead.
        const int MaxDepth = 200;

        public static object Deserialize(string json)
        {
            int pos = 0;
            var result = ParseValue(json, ref pos, 0);
            SkipWhitespace(json, ref pos);
            return result;
        }

        static object ParseValue(string s, ref int pos, int depth)
        {
            if (depth > MaxDepth) throw new FormatException($"JSON nested too deeply (>{MaxDepth}) at {pos}");
            SkipWhitespace(s, ref pos);
            if (pos >= s.Length) throw new FormatException("Unexpected end of JSON");
            char c = s[pos];
            switch (c)
            {
                case '{': return ParseObject(s, ref pos, depth);
                case '[': return ParseArray(s, ref pos, depth);
                case '"': return ParseString(s, ref pos);
                case 't': Expect(s, ref pos, "true"); return true;
                case 'f': Expect(s, ref pos, "false"); return false;
                case 'n': Expect(s, ref pos, "null"); return null;
                default: return ParseNumber(s, ref pos);
            }
        }

        static Dictionary<string, object> ParseObject(string s, ref int pos, int depth)
        {
            var dict = new Dictionary<string, object>();
            pos++; // '{'
            SkipWhitespace(s, ref pos);
            if (pos < s.Length && s[pos] == '}') { pos++; return dict; }
            while (true)
            {
                SkipWhitespace(s, ref pos);
                var key = ParseString(s, ref pos);
                SkipWhitespace(s, ref pos);
                if (pos >= s.Length || s[pos] != ':') throw new FormatException($"Expected ':' at {pos}");
                pos++;
                dict[key] = ParseValue(s, ref pos, depth + 1);
                SkipWhitespace(s, ref pos);
                if (pos >= s.Length) throw new FormatException("Unterminated object");
                if (s[pos] == ',') { pos++; continue; }
                if (s[pos] == '}') { pos++; return dict; }
                throw new FormatException($"Expected ',' or '}}' at {pos}");
            }
        }

        static List<object> ParseArray(string s, ref int pos, int depth)
        {
            var list = new List<object>();
            pos++; // '['
            SkipWhitespace(s, ref pos);
            if (pos < s.Length && s[pos] == ']') { pos++; return list; }
            while (true)
            {
                list.Add(ParseValue(s, ref pos, depth + 1));
                SkipWhitespace(s, ref pos);
                if (pos >= s.Length) throw new FormatException("Unterminated array");
                if (s[pos] == ',') { pos++; continue; }
                if (s[pos] == ']') { pos++; return list; }
                throw new FormatException($"Expected ',' or ']' at {pos}");
            }
        }

        static string ParseString(string s, ref int pos)
        {
            if (s[pos] != '"') throw new FormatException($"Expected string at {pos}");
            pos++;
            var sb = new StringBuilder();
            while (pos < s.Length)
            {
                char c = s[pos++];
                if (c == '"') return sb.ToString();
                if (c == '\\')
                {
                    if (pos >= s.Length) break;
                    char e = s[pos++];
                    switch (e)
                    {
                        case '"': sb.Append('"'); break;
                        case '\\': sb.Append('\\'); break;
                        case '/': sb.Append('/'); break;
                        case 'n': sb.Append('\n'); break;
                        case 'r': sb.Append('\r'); break;
                        case 't': sb.Append('\t'); break;
                        case 'b': sb.Append('\b'); break;
                        case 'f': sb.Append('\f'); break;
                        case 'u':
                            if (pos + 4 > s.Length) throw new FormatException("Bad \\u escape");
                            sb.Append((char)Convert.ToInt32(s.Substring(pos, 4), 16));
                            pos += 4;
                            break;
                        default: throw new FormatException($"Bad escape '\\{e}'");
                    }
                }
                else sb.Append(c);
            }
            throw new FormatException("Unterminated string");
        }

        static double ParseNumber(string s, ref int pos)
        {
            int start = pos;
            while (pos < s.Length && ("-+.eE0123456789".IndexOf(s[pos]) >= 0)) pos++;
            var slice = s.Substring(start, pos - start);
            if (!double.TryParse(slice, NumberStyles.Float, CultureInfo.InvariantCulture, out var d))
                throw new FormatException($"Bad number '{slice}' at {start}");
            return d;
        }

        static void Expect(string s, ref int pos, string literal)
        {
            if (pos + literal.Length > s.Length || s.Substring(pos, literal.Length) != literal)
                throw new FormatException($"Expected '{literal}' at {pos}");
            pos += literal.Length;
        }

        static void SkipWhitespace(string s, ref int pos)
        {
            while (pos < s.Length && char.IsWhiteSpace(s[pos])) pos++;
        }

        // -- typed accessors for parsed trees --

        public static Dictionary<string, object> AsObject(object v) => v as Dictionary<string, object>;
        public static List<object> AsList(object v) => v as List<object>;

        public static string GetString(Dictionary<string, object> obj, string key)
            => obj != null && obj.TryGetValue(key, out var v) ? v as string : null;

        /// CLAMPED, NOT CAST. `(int)d` for a double outside int's range is
        /// undefined in C#, and on x86 it yields int.MinValue — so a save
        /// carrying `"jobsDone": 9223372036854775807` restored to a job count
        /// of MINUS two billion. `SaveChaos` found twenty-four of these in one
        /// run and every single one had flipped sign, which is the worst shape
        /// an overflow can take: the number is not merely wrong, it is wrong in
        /// the direction that passes a `>= 0` check nowhere and a `< limit`
        /// check everywhere.
        ///
        /// Saturating keeps the sign and the magnitude's meaning. It is still a
        /// nonsense value — a save claiming two billion completed jobs is a
        /// corrupt save — but it is nonsense the callers' own range checks can
        /// see, rather than nonsense disguised as a small negative number.
        public static int GetInt(Dictionary<string, object> obj, string key)
        {
            if (obj == null || !obj.TryGetValue(key, out var v) || !(v is double d)) return 0;
            if (double.IsNaN(d)) return 0;
            if (d >= int.MaxValue) return int.MaxValue;
            if (d <= int.MinValue) return int.MinValue;
            return (int)d;
        }

        /// The same reading, but able to say "that key was not a number".
        ///
        /// `GetInt` returns 0 for absent, for null, for a string and for a
        /// genuine zero, which is right for the many optional fields that
        /// default to nothing and WRONG for the few that are load-bearing. A
        /// save whose `day` key had been deleted restored to day 0 — outside
        /// the range the entire rest of the game assumes, silently, and it
        /// would have failed days later somewhere else looking like a
        /// simulation bug.
        public static bool TryGetInt(Dictionary<string, object> obj, string key, out int value)
        {
            value = 0;
            if (obj == null || !obj.TryGetValue(key, out var v) || !(v is double d)) return false;
            if (double.IsNaN(d) || double.IsInfinity(d)) return false;
            value = GetInt(obj, key);
            return true;
        }

        public static Dictionary<string, object> GetObject(Dictionary<string, object> obj, string key)
            => obj != null && obj.TryGetValue(key, out var v) ? v as Dictionary<string, object> : null;

        public static List<object> GetList(Dictionary<string, object> obj, string key)
            => obj != null && obj.TryGetValue(key, out var v) ? v as List<object> : null;
    }
}
