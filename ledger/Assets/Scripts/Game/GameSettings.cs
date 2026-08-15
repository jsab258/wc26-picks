using System.Collections.Generic;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Player-facing settings, persisted next to the save. Deliberately small
    /// and plain-text like everything else in this project, so a player can
    /// open it, and so a corrupt file costs nothing.
    public class GameSettings
    {
        public float MasterVolume = 0.8f;
        public float MusicVolume = 0.5f;
        public float SfxVolume = 0.8f;
        /// SPEECH GETS ITS OWN FADER, and it is the one most likely to be
        /// moved. Voice sat on the sfx slider, which meant a player who
        /// wanted footsteps quieter got dialogue quieter too — and the
        /// reverse, which is worse, because turning speech up to hear it
        /// brings the whole street up with it. Defaults high: it is the
        /// channel everything else is authored to get out of the way of.
        public float VoiceVolume = 0.95f;
        /// Captions, 0 = off, 1 = speech, 2 = speech and sounds.
        ///
        /// OFF BY DEFAULT, and 2 is not a "more subtitles" setting — it is
        /// the one that makes `weapons-spec.md` §6.2's redundancy claim true
        /// for a deaf player, because three of its four "you have been
        /// noticed" channels are audio and only one of those is speech.
        public int Captions;
        public int TextScalePercent = 100;      // 80..150, accessibility
        public bool ColourblindSafe;            // swaps the credit/debit hues
        public float MouseSensitivity = 1.0f;
        /// Film grain, 0..1 of the authored amount. A slider rather than a
        /// fixed value because grain is the one post effect a meaningful
        /// number of people cannot tolerate, and an art choice that makes
        /// somebody unable to play is not an art choice.
        public float GrainAmount = 1.0f;
        /// Graphics preset. See Core/Detail for what each level gives up and
        /// why the crowd is not what gets cut.
        public int Detail = (int)Ledger.Core.Detail.Default;
        public bool ShowOdds = true;            // qualitative reads before risky moves

        /// Rebindable actions. Names are what the help line prints.
        public readonly Dictionary<string, KeyCode> Keys = new Dictionary<string, KeyCode>
        {
            { "Talk", KeyCode.E },
            { "Ledger", KeyCode.L },
            { "Plan", KeyCode.J },
            { "Coat", KeyCode.C },
            { "Drive", KeyCode.F },
            { "Phone", KeyCode.T },
            { "Save", KeyCode.F5 },
            { "Debug", KeyCode.F1 },
            { "Pause", KeyCode.Escape },
        };

        public KeyCode Key(string action) =>
            Keys.TryGetValue(action, out var k) ? k : KeyCode.None;

        public void Rebind(string action, KeyCode key)
        {
            if (!Keys.ContainsKey(action)) return;
            // No two actions may share a key: the previous owner loses it.
            foreach (var pair in new List<KeyValuePair<string, KeyCode>>(Keys))
                if (pair.Value == key && pair.Key != action) Keys[pair.Key] = KeyCode.None;
            Keys[action] = key;
        }

        public string Serialize()
        {
            var keys = new Dictionary<string, object>();
            foreach (var pair in Keys) keys[pair.Key] = (int)pair.Value;
            return MiniJson.Serialize(new Dictionary<string, object>
            {
                { "master", MasterVolume }, { "music", MusicVolume }, { "sfx", SfxVolume },
                { "voice", VoiceVolume }, { "captions", Captions },
                { "textScale", TextScalePercent }, { "colourblind", ColourblindSafe },
                { "sensitivity", MouseSensitivity }, { "grain", GrainAmount },
                { "detail", Detail },
                { "showOdds", ShowOdds },
                { "keys", keys },
            });
        }

        public static GameSettings Deserialize(string json)
        {
            var s = new GameSettings();
            try
            {
                var root = MiniJson.AsObject(MiniJson.Deserialize(json));
                if (root == null) return s;
                s.MasterVolume = Num(root, "master", s.MasterVolume);
                s.MusicVolume = Num(root, "music", s.MusicVolume);
                s.SfxVolume = Num(root, "sfx", s.SfxVolume);
                // Absent in every settings file written before speech had a
                // bus, so the default has to survive the round trip rather
                // than silently reading as zero and muting all dialogue.
                s.VoiceVolume = Num(root, "voice", s.VoiceVolume);
                s.Captions = (int)Num(root, "captions", s.Captions);
                s.TextScalePercent = root.ContainsKey("textScale") ? MiniJson.GetInt(root, "textScale") : s.TextScalePercent;
                s.ColourblindSafe = root.TryGetValue("colourblind", out var cb) && cb is bool b && b;
                s.MouseSensitivity = Num(root, "sensitivity", s.MouseSensitivity);
                s.GrainAmount = Num(root, "grain", s.GrainAmount);
                s.Detail = (int)Num(root, "detail", s.Detail);
                s.ShowOdds = !root.TryGetValue("showOdds", out var so) || !(so is bool sb) || sb;
                var keys = MiniJson.GetObject(root, "keys");
                if (keys != null)
                    foreach (var pair in keys)
                        if (s.Keys.ContainsKey(pair.Key) && pair.Value != null)
                            s.Keys[pair.Key] = (KeyCode)System.Convert.ToInt32(pair.Value);
            }
            catch (System.Exception) { /* a broken settings file is just defaults */ }
            return s;
        }

        static float Num(Dictionary<string, object> d, string k, float fallback) =>
            d.TryGetValue(k, out var v) && v != null ? (float)System.Convert.ToDouble(v) : fallback;

        // ---- disk ----

        public static string Path => System.IO.Path.Combine(Application.persistentDataPath, "settings.json");
        static GameSettings _current;

        public static GameSettings Current
        {
            get
            {
                if (_current != null) return _current;
                try
                {
                    _current = System.IO.File.Exists(Path)
                        ? Deserialize(System.IO.File.ReadAllText(Path))
                        : new GameSettings();
                }
                catch (System.Exception) { _current = new GameSettings(); }
                // THE SIM RENDERS AT HIGH, ALWAYS — pinned here, in the one
                // place every reader goes through, the moment the settings
                // materialise. `Detail.Default` went to Medium on 15 Aug for
                // first-run machines, and CI has no settings file, so without
                // this pin every committed still would have quietly switched
                // to Medium: shorter shafts, nearer shadows — and every
                // lighting number in the verdict history would sit on the
                // other side of a regime change nothing announced. The stills
                // judge the ART, and the art is judged at full detail; what a
                // first-run player defaults to is a separate question with a
                // separate answer.
                if (SimMode.Days > 0)
                    _current.Detail = (int)Ledger.Core.DetailLevel.High;
                return _current;
            }
        }

        public void Save()
        {
            try { System.IO.File.WriteAllText(Path, Serialize()); }
            catch (System.Exception e) { Debug.LogWarning($"settings not saved: {e.Message}"); }
        }
    }
}
