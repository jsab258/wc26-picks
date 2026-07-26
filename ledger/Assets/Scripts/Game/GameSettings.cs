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
        public int TextScalePercent = 100;      // 80..150, accessibility
        public bool ColourblindSafe;            // swaps the credit/debit hues
        public float MouseSensitivity = 1.0f;
        public bool ShowOdds = true;            // qualitative reads before risky moves

        /// Rebindable actions. Names are what the help line prints.
        public readonly Dictionary<string, KeyCode> Keys = new Dictionary<string, KeyCode>
        {
            { "Talk", KeyCode.E },
            { "Ledger", KeyCode.L },
            { "Plan", KeyCode.J },
            { "Coat", KeyCode.C },
            { "Drive", KeyCode.F },
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
                { "textScale", TextScalePercent }, { "colourblind", ColourblindSafe },
                { "sensitivity", MouseSensitivity }, { "showOdds", ShowOdds },
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
                s.TextScalePercent = root.ContainsKey("textScale") ? MiniJson.GetInt(root, "textScale") : s.TextScalePercent;
                s.ColourblindSafe = root.TryGetValue("colourblind", out var cb) && cb is bool b && b;
                s.MouseSensitivity = Num(root, "sensitivity", s.MouseSensitivity);
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
