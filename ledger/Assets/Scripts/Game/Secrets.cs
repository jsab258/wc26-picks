using System;
using System.Collections.Generic;
using System.IO;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// API key storage: environment variable first (dev), then a json file in
    /// the per-user data folder (playtester path — filled in by the in-game
    /// prompt on first run). Never ships inside the build or the repo.
    public static class Secrets
    {
        static string FilePath => Path.Combine(Application.persistentDataPath, "secrets.json");

        public static string LoadAnthropicKey()
        {
            var env = Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY");
            if (!string.IsNullOrEmpty(env)) return env;

            try
            {
                if (File.Exists(FilePath))
                {
                    var root = MiniJson.AsObject(MiniJson.Deserialize(File.ReadAllText(FilePath)));
                    var key = MiniJson.GetString(root, "anthropic_api_key");
                    if (!string.IsNullOrEmpty(key)) return key;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"Secrets: could not read {FilePath}: {e.Message}");
            }
            return null;
        }

        public static void SaveAnthropicKey(string key)
        {
            var json = MiniJson.Serialize(new Dictionary<string, object> { { "anthropic_api_key", key.Trim() } });
            File.WriteAllText(FilePath, json);
        }
    }
}
