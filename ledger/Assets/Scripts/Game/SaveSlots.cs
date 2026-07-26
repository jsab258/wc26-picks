using System;
using System.IO;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Save files on disk (production track P2). One autosave plus manual
    /// slots, each readable plain JSON, each carrying a version the codec can
    /// migrate. A corrupt file is quarantined rather than deleted — a player's
    /// week is worth more than a tidy folder.
    public static class SaveSlots
    {
        public const int ManualSlots = 3;

        public static string Dir => Application.persistentDataPath;
        public static string AutoPath => Path.Combine(Dir, "ledger-save.json");
        public static string SlotPath(int slot) => Path.Combine(Dir, $"ledger-save-{slot}.json");

        public static bool HasAny()
        {
            try
            {
                if (File.Exists(AutoPath)) return true;
                for (int i = 1; i <= ManualSlots; i++) if (File.Exists(SlotPath(i))) return true;
            }
            catch (Exception) { }
            return false;
        }

        /// The newest readable save, or null. "Continue" uses this.
        public static string NewestPath()
        {
            string best = null;
            DateTime bestTime = DateTime.MinValue;
            try
            {
                foreach (var p in AllPaths())
                {
                    if (!File.Exists(p)) continue;
                    var t = File.GetLastWriteTimeUtc(p);
                    if (t <= bestTime) continue;
                    bestTime = t; best = p;
                }
            }
            catch (Exception) { }
            return best;
        }

        static string[] AllPaths()
        {
            var paths = new string[ManualSlots + 1];
            paths[0] = AutoPath;
            for (int i = 1; i <= ManualSlots; i++) paths[i] = SlotPath(i);
            return paths;
        }

        /// One line for the menu: what continuing would actually resume.
        public static string Describe()
        {
            var path = NewestPath();
            if (path == null) return "No saved city. A new game starts on the morning you inherit the bar.";
            try
            {
                var json = File.ReadAllText(path);
                int version = SaveCodec.PeekVersion(json);
                if (version == 0) return "A save exists but cannot be read. Starting new will not touch it.";
                if (version > SaveCodec.Version) return "That save was written by a newer build of the game.";
                var root = MiniJson.AsObject(MiniJson.Deserialize(json));
                int day = root != null ? MiniJson.GetInt(root, "day") : 0;
                bool open = root != null && root.TryGetValue("openMode", out var om) && om is bool b && b;
                return open
                    ? $"The open city, day {day}. Nobody is counting anymore."
                    : $"Day {day} of the first week.";
            }
            catch (Exception) { return "A save exists but cannot be read."; }
        }

        /// Corruption recovery: move the bad file aside so the player can start
        /// again without losing the chance of hand-recovering it later.
        public static void Quarantine(string path)
        {
            try
            {
                if (!File.Exists(path)) return;
                var bad = path + ".corrupt";
                if (File.Exists(bad)) File.Delete(bad);
                File.Move(path, bad);
                Debug.LogWarning($"Save quarantined to {bad}");
            }
            catch (Exception e) { Debug.LogError($"Could not quarantine save: {e.Message}"); }
        }

        public static void DeleteAll()
        {
            foreach (var p in AllPaths())
                try { if (File.Exists(p)) File.Delete(p); } catch (Exception) { }
        }
    }
}
