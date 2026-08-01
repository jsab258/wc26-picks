using System.Collections.Generic;
using System.IO;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// Loads the generated Tier-2 batch (game-design/tier2-batch-1.json, shipped
    /// in StreamingAssets) and turns a curated subset into walking, talking,
    /// gossiping residents. The generator decided who exists; this instantiates
    /// them. Curation happens here as data: which ids walk now (scene cost),
    /// which are skipped (id collisions where the hand-authored ring wins).
    public static class Tier2Batch
    {
        /// Walking now — chosen for occupation spread across the district.
        /// The other ~45 stay data until wanted; "no non-characters, only
        /// characters nobody has looked at yet."
        static readonly string[] LiveIds =
        {
            "petra", "tomas", "magda", "bruno", "sanja", "goran", "katarina",
            "stipe", "drago", "hana", "zora", "franjo", "danica", "luka",
            // Second wave (round 2): filling the district's daily texture.
            "dusan", "iva", "fabjan", "ines", "dario", "selma", "filip", "tanja",
            "marta", "jelena",
        };

        // Ring cards and reserved Tier-1 names outrank batch ids.
        static readonly HashSet<string> Skipped = new HashSet<string> { "vesna", "tibor", "emil", "viktor" };

        class Member
        {
            public string Id, Name;
            public CastMember Cast;
            public (GameTime, Vector3)[] Schedule;
            public List<(string to, double weight)> Links = new List<(string, double)>();
            public Secret Secret;
            public string Need;
        }

        static readonly Dictionary<string, Member> _members = new Dictionary<string, Member>();
        public static bool Loaded { get; private set; }

        public static IEnumerable<string> LiveNames { get { Load(); foreach (var m in _members.Values) yield return m.Name; } }

        public static CastMember Get(string name)
        {
            Load();
            foreach (var m in _members.Values) if (m.Name == name) return m.Cast;
            return null;
        }

        public static bool TryNeed(string name, out int cost, out string line)
        {
            Load();
            foreach (var m in _members.Values)
                if (m.Name == name && !string.IsNullOrEmpty(m.Need))
                {
                    cost = 120;
                    line = $"You sort it quietly: {m.Need.TrimEnd('.')}.";
                    return true;
                }
            cost = 0; line = null; return false;
        }

        public static IEnumerable<Secret> Secrets()
        {
            Load();
            foreach (var m in _members.Values) if (m.Secret != null) yield return m.Secret;
        }

        public static IEnumerable<(string a, string b, double w)> GraphLinks()
        {
            Load();
            foreach (var m in _members.Values)
                foreach (var (to, w) in m.Links)
                    yield return (m.Name, to, w);
        }

        /// Spawns the live subset as walkers; GameController's generic host loop
        /// (CastSetup -> Tier2Setup -> Tier2Batch lookup) gives them brains.
        public static List<NpcWalker> SpawnWalkers()
        {
            Load();
            var walkers = new List<NpcWalker>();
            foreach (var m in _members.Values)
            {
                if (m.Schedule == null || m.Schedule.Length == 0) continue;
                walkers.Add(NpcWalker.Spawn(m.Name, ColorFor(m.Id), m.Schedule));
            }
            return walkers;
        }

        static Color ColorFor(string id)
        {
            int h = 17;
            foreach (var ch in id) h = h * 31 + ch;
            // "Muted, distinct street clothes — never brighter than the cast"
            // is what this said while running the hue over the ENTIRE wheel at
            // saturation 0.35 and value 0.55, with nothing enforcing either
            // claim. `PopulationHost` said the same thing and used 0.22/0.45,
            // so which crowd a walker belonged to decided how loud their coat
            // was. `Core/Wardrobe` is the one source now, and the promise is a
            // number CoreTests holds rather than a sentence.
            Wardrobe.Dress(Mathf.Abs(h % 3600) / 3600.0,
                           out double wh, out double ws, out double wv);
            return Color.HSVToRGB((float)wh, (float)ws, (float)wv);
        }

        static void Load()
        {
            if (Loaded) return;
            Loaded = true;
            try
            {
                var path = Path.Combine(Application.streamingAssetsPath, "tier2-batch-1.json");
                if (!File.Exists(path)) { Debug.LogWarning("Tier2Batch: manifest missing; district walks empty."); return; }
                var list = MiniJson.AsList(MiniJson.Deserialize(File.ReadAllText(path)));
                if (list == null) return;
                var live = new HashSet<string>(LiveIds);
                foreach (var o in list)
                {
                    var card = MiniJson.AsObject(o);
                    if (card == null) continue;
                    var id = MiniJson.GetString(card, "id");
                    if (id == null || Skipped.Contains(id) || !live.Contains(id)) continue;
                    var m = Parse(card);
                    if (m != null) _members[m.Id] = m;
                }
                Debug.Log($"Tier2Batch: {_members.Count} residents walking from the generated batch.");
            }
            catch (System.Exception e) { Debug.LogError($"Tier2Batch load failed: {e.Message}"); }
        }

        static Member Parse(Dictionary<string, object> card)
        {
            var id = MiniJson.GetString(card, "id");
            var name = MiniJson.GetString(card, "name");
            var traits = MiniJson.GetObject(card, "traits");
            if (id == null || name == null || traits == null) return null;

            var facts = new System.Text.StringBuilder();
            foreach (var f in MiniJson.GetList(card, "hardFacts") ?? new List<object>())
                facts.AppendLine($"- {f}");
            var occupation = MiniJson.GetString(card, "occupation") ?? "resident";
            var cast = new CastMember
            {
                Circle = MiniJson.GetString(card, "circle") ?? "day",
                Greed = Num(traits, "greed"), Nerve = Num(traits, "nerve"), Loyalty = Num(traits, "loyalty"),
                Scene = $"About the Hook — the {occupation}'s rounds — talking with the new landlord.",
                Card = $"# {name}\nid: {id}\ntier: ambient\n\n## Summary\n{MiniJson.GetString(card, "summary")}\n\n" +
                       $"## Personality\n{MiniJson.GetString(card, "personality")}\n\n" +
                       $"## Speech Style\n{MiniJson.GetString(card, "speech")}\n\n## Hard Facts\n{facts}",
            };

            var m = new Member { Id = id, Name = name, Cast = cast, Need = MiniJson.GetString(card, "need") };

            var stops = new List<(GameTime, Vector3)>();
            foreach (var s in MiniJson.GetList(card, "schedule") ?? new List<object>())
            {
                var so = MiniJson.AsObject(s);
                var place = so != null ? HookMap.Get(MiniJson.GetString(so, "place")) : null;
                if (place == null) continue;
                stops.Add((new GameTime(0, MiniJson.GetInt(so, "hour"), 0), new Vector3((float)place.X, 0, (float)place.Z)));
            }
            m.Schedule = stops.ToArray();

            foreach (var c in MiniJson.GetList(card, "connections") ?? new List<object>())
            {
                var co = MiniJson.AsObject(c);
                var to = co != null ? MiniJson.GetString(co, "to") : null;
                if (to == null) continue;
                // Link by display name; targets resolve at Begin only if live.
                m.Links.Add((char.ToUpperInvariant(to[0]) + to.Substring(1), Num(co, "weight")));
            }

            var secret = MiniJson.GetObject(card, "secret");
            if (secret != null)
            {
                var sec = new Secret
                {
                    Id = $"{id}_batch", OwnerId = name,
                    Kind = MiniJson.GetString(secret, "kind") == "criminal" ? SecretKind.Criminal : SecretKind.Shameful,
                    Summary = MiniJson.GetString(secret, "line") ?? "",
                };
                foreach (var k in (MiniJson.GetList(secret, "knownBy") ?? new List<object>()))
                    if (k is string ks && ks.Length > 0)
                        sec.KnownBy.Add(char.ToUpperInvariant(ks[0]) + ks.Substring(1));
                m.Secret = sec;
            }
            return m;
        }

        static double Num(Dictionary<string, object> d, string key) =>
            d != null && d.TryGetValue(key, out var v) && v != null ? System.Convert.ToDouble(v) : 0.5;
    }
}
