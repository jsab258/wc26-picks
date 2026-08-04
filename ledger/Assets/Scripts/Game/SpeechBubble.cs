using System.Collections.Generic;
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
            var b = go.AddComponent<SpeechBubble>();
            b._follow = speaker;
            b._base = colour;
            // STACKED, NOT OVERLAPPED, AND NEVER HIDDEN.
            //
            // `collidingBubbles=15` beside `bubblesOnScreen=6` is the whole
            // argument: six bubbles have exactly fifteen possible pairs, so
            // EVERY pair was overlapping. `collidingNames=0` in the same run —
            // the nameplate declutter is perfect — which made "offer bubbles to
            // NameTags" the obvious fix and the wrong one. That declutter HIDES
            // what it cannot place, and its own comment says why that is right
            // for a name: putting a name over the wrong person is a lie, and
            // this game is about who saw whom.
            //
            // A line is not a name. A hidden nameplate costs you nothing you
            // cannot get by walking closer; a hidden bubble costs you the words,
            // and the words are the content. So bubbles stack UPWARD instead,
            // which cannot lose anything — the worst case is a line sitting a
            // little higher over the head it belongs to, and it still follows
            // that head every frame.
            b._lift = StackHeightNear(speaker.position);
            go.transform.position = speaker.position + Vector3.up * (2.05f + b._lift);

            b._text = go.AddComponent<TextMesh>();
            b._text.text = Wrap(line, 34);
            b._text.characterSize = 0.05f;
            b._text.fontSize = 46;
            b._text.anchor = TextAnchor.LowerCenter;
            b._text.alignment = TextAlignment.Center;
            b._text.color = colour;

            // AND THIS ONE DELIBERATELY DOES NOT TAKE `WorldText`. Every other
            // TextMesh in the game was moved onto a depth-testing shader
            // because a name has a place in the world and should go behind
            // what its owner goes behind. A spoken line does not: it is a
            // thing you HEARD, and occlusion is already modelled here as
            // clarity, on purpose — a shout through an open door still reads
            // and a murmur behind glass does not. Depth-testing it would hide
            // the shout entirely and say the opposite of what the ear did.
            //
            // AND IT GIVES UP THE BACK-FACE CULL WITH IT, WHICH THIS DID NOT
            // SAY. The reasoning above is entirely about `ZTest`, and it is
            // right — but `Hidden/LedgerText` also sets `Cull Back`, and the
            // built-in text shader is `Cull Off`. So a bubble is the ONE kind of
            // world text in this game that renders its own reverse when you get
            // behind it, and `textMirrored` counts exactly that population
            // because the shader test is what puts a label in it.
            //
            // That is why the aim mattering at shot time mattered at all: a
            // nameplate aimed a frame late is skewed, and a bubble aimed a frame
            // late can be printed backwards. Accepted rather than fixed — the
            // fix is a third shader with LedgerText's cull and the built-in's
            // depth behaviour, which is worth doing the day the number says
            // bubbles are being read backwards rather than the day it occurs to
            // somebody.
            //
            // A line you only half caught is also a line you can barely see.
            // Fading with clarity rather than with distance means a shout
            // through an open door still reads, and a murmur behind glass
            // does not, which is what the ear would have told you.
            b._base.a = Mathf.Clamp01(0.35f + 0.65f * (float)clarity);
            b._text.color = b._base;

            b._until = Time.time + seconds;
            b._fadeFrom = seconds * 0.7f;
            // AIMED ONCE HERE, BEFORE ANY FRAME DRAWS IT. A bubble created
            // during `Update` gets its first `LateUpdate` after the frame it was
            // born in has already been rendered — so without this it spends its
            // first frame at identity rotation, facing world north, which is a
            // mirror image from anywhere south of the speaker.
            Billboard.Register(go.transform);
            Billboard.Aim(go.transform, Camera.main);
            _live.Add(b);
            return b;
        }

        /// Every bubble currently alive, so a new one can see what it would
        /// land on top of. Registered on creation, swept lazily on read —
        /// destroyed Unity objects compare equal to null and a list of them
        /// would otherwise grow for the life of the process.
        static readonly List<SpeechBubble> _live = new List<SpeechBubble>();

        /// The lift this bubble carries above its speaker's head.
        float _lift;

        /// How far up a new bubble has to start to clear the ones already
        /// talking near this spot.
        ///
        /// WORLD SPACE, NOT SCREEN SPACE, and deliberately: a screen-space test
        /// would have to be redone every frame as the camera moves, and a line
        /// that jumps up and down while somebody walks past is worse than one
        /// that overlaps. Speakers within `CrowdMetres` of each other are the
        /// ones whose bubbles can plausibly collide from any angle, which is
        /// the conservative choice — it lifts a few lines that did not need it
        /// and never fails to lift one that did.
        const float CrowdMetres = 4.0f;
        const float LineLift = 0.45f;
        const float MaxLift = 1.8f;      // four lines; past that a crowd is a crowd

        static float StackHeightNear(Vector3 at)
        {
            float lift = 0f;
            for (int i = _live.Count - 1; i >= 0; i--)
            {
                var b = _live[i];
                if (b == null || b._follow == null) { _live.RemoveAt(i); continue; }
                if (Vector3.Distance(b._follow.position, at) > CrowdMetres) continue;
                // Sit above the highest thing already in this huddle rather than
                // counting heads: two bubbles that already stacked leave a gap
                // at the bottom, and filling it would put the third one back on
                // top of the first.
                if (b._lift + LineLift > lift) lift = b._lift + LineLift;
            }
            return Mathf.Min(lift, MaxLift);
        }

        /// How flat the flattest spoken line got, over the run. Starts above 1
        /// so "never measured" cannot be mistaken for "perfectly upright".
        public static double WorstUpDot = 2.0;

        void LateUpdate()
        {
            if (_follow == null) { Destroy(gameObject); return; }
            // The lift is part of where this line lives, so it is reapplied
            // every frame with the follow. Setting it once at creation and
            // letting this line overwrite it was the first draft, and the
            // bubble dropped back onto its neighbour on the very next frame.
            transform.position = _follow.position + Vector3.up * (2.05f + _lift);

            // YAW ONLY, AND THIS WAS THE SECOND SITE OF A BUG THAT WAS FIXED
            // ONCE AND NEVER GREPPED FOR — so the maths now lives in exactly one
            // place and this calls it. `Billboard` carries the paragraph about
            // the degenerate basis and the paragraph about why the SHOT has to
            // re-aim as well; both are about this object.
            Billboard.Aim(transform, Camera.main);

            // PROVEN, NOT ASSERTED. Dot of the bubble's own up-vector with
            // world up: 1.0 standing, 0.0 flat on the ground. Worst over the
            // run, because one line lying down is the fault.
            //
            // AND IT ANSWERS A NARROWER QUESTION THAN IT LOOKS. It is sampled
            // one line after the aim, so it reports the rotation this method
            // just set — never the rotation the committed still was rendered
            // at, which is the previous frame's. `speechUpDot=1.000` sat beside
            // a frame with two lines printed backwards and both were true.
            // `billboardsStale` is the number for the picture; this one only
            // says the aim itself is not degenerate.
            double up = Vector3.Dot(transform.up, Vector3.up);
            if (up < WorstUpDot) WorstUpDot = up;

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
