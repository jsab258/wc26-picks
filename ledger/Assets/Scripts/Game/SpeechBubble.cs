using Ledger.Core;
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

        /// EARSHOT IS NOT A RADIUS (game-feel-spec.md §4, Acoustics).
        ///
        /// This used to be a hard cut: inside six metres you read the line in
        /// full, outside it you saw nothing. Both halves are wrong. Half-
        /// hearing a sentence is not the same as hearing it quietly, and a
        /// distant line rendered at full text in a smaller font tells the
        /// player they have perfect ears and only bad eyes.
        ///
        /// So the line is now filtered through what the listener could
        /// actually have got: distance, whether a wall is in the way, and how
        /// loud the street is. Words drop out; the gaps are ellipses. It is a
        /// better hook than certainty ever was, because a sentence with a
        /// hole in it makes you walk closer — which is the entire mechanic.
        /// SPEAKING IS A SOUND, and until now it was not.
        ///
        /// Every spoken line in the game funnels through here — the ambient
        /// exchange, the recognition line, the delayed reply — so this is where
        /// the city gets told, for the same reason the noise ring lives inside
        /// `Perceivers.Emit`: no call site should be able to speak without the
        /// street being able to hear it. Wiring it at the three call sites
        /// instead would mean the fourth one, written next month, is silent.
        ///
        /// Loudness is a real argument rather than a constant because the
        /// difference between two people talking and one of them calling across
        /// a pavement is exactly the difference the masking model exists to
        /// express: at 3am both carry, at noon only the second does.
        public static SpeechBubble Say(Transform speaker, string line, float seconds,
                                       Color colour, double loudness, string speakerId = null)
        {
            if (speaker != null)
                Perceivers.Emit(speaker.position, loudness, "speech");
            return SayQuietly(speaker, line, seconds, colour, speakerId);
        }

        /// The bubble with no sound — for anything that is written rather than
        /// said. Named so that using it is a decision.
        public static SpeechBubble SayQuietly(Transform speaker, string line, float seconds,
                                              Color colour, string speakerId = null)
        {
            if (speaker == null || string.IsNullOrEmpty(line)) return null;
            string spoken = line;

            var ear = Camera.main;
            double clarity = 1.0;
            if (ear != null)
            {
                var head = speaker.position + Vector3.up * 1.7f;
                float metres = Vector3.Distance(ear.transform.position, head);
                bool wall = Physics.Linecast(ear.transform.position, head, out var hit,
                                             ~0, QueryTriggerInteraction.Ignore)
                            && hit.transform != speaker && !hit.transform.IsChildOf(speaker);
                clarity = Acoustics.Intelligibility(metres, wall, Audio.ChatterLevel);

                // AND IT IS ALSO A SOUND YOU HEAR, not only a caption. The
                // bank does not exist yet, so this asks for a recording that
                // is almost always absent — deliberately, and counted, so the
                // day the bank lands nothing needs wiring and until then the
                // silence is a measurement rather than an assumption.
                Audio.Speak(VoiceBank.ClipName(
                                VoiceBank.VoiceFor(speakerId ?? speaker.name, VoiceBank.Cast),
                                spoken),
                            metres, wall, Audio.ChatterLevel);

                // A STABLE SEED, not `string.GetHashCode()`. That is
                // randomised per process in modern .NET and stable in Unity's
                // runtime only by accident of which runtime it is — so the
                // same line half-heard would drop different words after an
                // engine update, for no reason anybody could trace.
                line = Acoustics.AsHeard(line, clarity, VoiceBank.SeedFor(spoken) % 9973);
                // Nothing usable came through. You heard talking, not words —
                // and showing a bubble anyway would be the game telling you
                // something the character did not learn.
                if (line == null) return null;
            }

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

            // A line you only half caught is also a line you can barely see.
            // Fading with clarity rather than with distance means a shout
            // through an open door still reads, and a murmur behind glass
            // does not, which is what the ear would have told you.
            b._base.a = Mathf.Clamp01(0.35f + 0.65f * (float)clarity);
            b._text.color = b._base;

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
