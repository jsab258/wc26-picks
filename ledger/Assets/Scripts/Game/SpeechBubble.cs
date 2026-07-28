using UnityEngine;

namespace Ledger.Game
{
    /// A line of speech, in the world, over the person saying it (M15.1).
    ///
    /// Deliberately NOT a UI panel. The whole point of this milestone is that
    /// the player reads the street rather than an interface: a line has to
    /// live where its speaker is standing, be missable, and go away on its
    /// own. If you were not there, you did not hear it.
    ///
    /// Text is world-space and billboarded, sized so it is comfortable at
    /// conversational distance and unreadable across the district — you have
    /// to be near people to know what they are saying, which is the mechanic.
    public class SpeechBubble : MonoBehaviour
    {
        TextMesh _text;
        float _until;
        float _fadeFrom;
        Transform _follow;
        Color _base;

        public static SpeechBubble Say(Transform speaker, string line, float seconds, Color colour)
        {
            if (speaker == null || string.IsNullOrEmpty(line)) return null;

            var go = new GameObject("Speech");
            go.transform.position = speaker.position + Vector3.up * 2.05f;
            var b = go.AddComponent<SpeechBubble>();
            b._follow = speaker;
            b._base = colour;

            b._text = go.AddComponent<TextMesh>();
            b._text.text = Wrap(line, 34);
            b._text.characterSize = 0.05f;
            b._text.fontSize = 46;
            b._text.anchor = TextAnchor.LowerCenter;
            b._text.alignment = TextAlignment.Center;
            b._text.color = colour;

            b._until = Time.time + seconds;
            b._fadeFrom = seconds * 0.7f;
            return b;
        }

        void LateUpdate()
        {
            if (_follow == null) { Destroy(gameObject); return; }
            transform.position = _follow.position + Vector3.up * 2.05f;

            var cam = Camera.main;
            if (cam != null)
                transform.rotation = Quaternion.LookRotation(transform.position - cam.transform.position);

            float left = _until - Time.time;
            if (left <= 0f) { Destroy(gameObject); return; }
            // Fade the last stretch, so lines leave rather than blink out.
            if (left < _fadeFrom && _text != null)
            {
                var c = _base;
                c.a = Mathf.Clamp01(left / _fadeFrom);
                _text.color = c;
            }
        }

        /// Hard wrap at roughly a comfortable reading width. TextMesh has no
        /// wrapping of its own and a long line otherwise runs off across the
        /// street, over other people's heads.
        static string Wrap(string s, int width)
        {
            if (string.IsNullOrEmpty(s) || s.Length <= width) return s;
            var sb = new System.Text.StringBuilder(s.Length + 8);
            int since = 0;
            foreach (var word in s.Split(' '))
            {
                if (since > 0 && since + word.Length + 1 > width) { sb.Append('\n'); since = 0; }
                else if (since > 0) { sb.Append(' '); since++; }
                sb.Append(word);
                since += word.Length;
            }
            return sb.ToString();
        }
    }
}
