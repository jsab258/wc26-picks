using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// P5: consequences persist — the city's state IS the save file. The codec
    /// overlays state onto freshly-authored objects (cards, beats, secrets and
    /// gossipers are rebuilt by the bootstrap; the save carries only what play
    /// changed). NPC memories persist separately as markdown and are not here.
    public static class SaveCodec
    {
        public const int Version = 1;

        public static string Capture(GameTime now, Wallet wallet, Campaign camp,
            PlayerKnowledge knowledge, SecretsBook secrets, BeatBook beats,
            GossipMill mill, DebtBook debts, Dictionary<string, object> extra)
        {
            var root = new Dictionary<string, object>
            {
                { "version", Version },
                { "day", now.Day }, { "hour", now.Hour }, { "minute", now.Minute },
                { "clean", wallet.Clean }, { "dirty", wallet.Dirty }, { "washed", wallet.TotalWashed },
                { "patience", camp.OutfitPatience }, { "exposedStreak", camp.ExposedStreak },
                { "jobsDone", camp.JobsDone }, { "jobsMissed", camp.JobsMissed },
                { "daysClosed", camp.DaysClosed }, { "verdict", camp.Verdict.ToString() },
                { "verdictReason", camp.VerdictReason },
                { "extra", extra ?? new Dictionary<string, object>() },
            };

            root["knowledge"] = knowledge.Entries.Select(k => (object)new Dictionary<string, object>
            {
                { "holderId", k.HolderId }, { "holderName", k.HolderName }, { "topic", k.TopicKey },
                { "summary", k.Summary }, { "source", k.Source }, { "conf", k.ConfidenceWhenLearned },
                { "learnedAt", (double)k.LearnedAt.TotalMinutes }, { "sensitive", k.Sensitive },
                { "handled", k.Handled },
            }).ToList();

            root["secrets"] = secrets.All.Select(s => (object)new Dictionary<string, object>
            {
                { "id", s.Id }, { "known", s.KnownToPlayer }, { "spent", s.HookSpent },
                { "from", s.LearnedFrom ?? "" }, { "learnedAt", (double)s.LearnedAt.TotalMinutes },
            }).ToList();

            root["beats"] = beats.All.Select(b => (object)new Dictionary<string, object>
            {
                { "id", b.Id }, { "state", b.State.ToString() },
            }).ToList();

            root["debts"] = (debts != null ? debts.All : Enumerable.Empty<Debtor>())
                .Select(d => (object)new Dictionary<string, object>
                {
                    { "id", d.Id }, { "collected", d.Collected }, { "forgiven", d.Forgiven },
                    { "lastAskedDay", d.LastAskedDay },
                }).ToList();

            root["discredited"] = mill.DiscreditedTopics.Cast<object>().ToList();
            root["agents"] = mill.Agents.Select(a => (object)new Dictionary<string, object>
            {
                { "id", a.Id }, { "loyalty", a.Loyalty }, { "leashed", a.Leashed },
                { "suspicion", a.Suspicion.Value },
                { "suppressed", a.Suppressed.Cast<object>().ToList() },
                { "rumors", a.Rumors.Select(r => (object)new Dictionary<string, object>
                    {
                        { "subj", r.Content.Subject }, { "pred", r.Content.Predicate }, { "val", r.Content.Value },
                        { "origin", r.OriginId }, { "summary", r.Summary }, { "conf", r.Confidence },
                        { "hops", r.Hops }, { "sensitive", r.Sensitive },
                    }).ToList() },
                { "facts", a.Knowledge.Facts.Select(f => (object)new Dictionary<string, object>
                    {
                        { "subj", f.Subject }, { "pred", f.Predicate }, { "val", f.Value },
                    }).ToList() },
            }).ToList();

            return MiniJson.Serialize(root);
        }

        /// Overlays a save onto freshly-authored objects. Returns the saved clock;
        /// unknown ids in the save are skipped (authored content may have changed).
        public static GameTime Restore(string json, Wallet wallet, Campaign camp,
            PlayerKnowledge knowledge, SecretsBook secrets, BeatBook beats,
            GossipMill mill, DebtBook debts, out Dictionary<string, object> extra)
        {
            var root = MiniJson.AsObject(MiniJson.Deserialize(json));
            if (root == null) throw new Exception("save file unreadable");
            extra = MiniJson.GetObject(root, "extra") ?? new Dictionary<string, object>();

            var now = new GameTime(MiniJson.GetInt(root, "day"), MiniJson.GetInt(root, "hour"), MiniJson.GetInt(root, "minute"));
            wallet.Restore(MiniJson.GetInt(root, "clean"), MiniJson.GetInt(root, "dirty"), MiniJson.GetInt(root, "washed"));

            Enum.TryParse(MiniJson.GetString(root, "verdict"), out Verdict verdict);
            camp.Restore(Num(root, "patience"), MiniJson.GetInt(root, "exposedStreak"),
                MiniJson.GetInt(root, "jobsDone"), MiniJson.GetInt(root, "jobsMissed"),
                MiniJson.GetInt(root, "daysClosed"), verdict, MiniJson.GetString(root, "verdictReason"));

            foreach (var o in MiniJson.GetList(root, "knowledge") ?? new List<object>())
            {
                var k = MiniJson.AsObject(o);
                if (k == null) continue;
                knowledge.Restore(new KnownLead
                {
                    HolderId = MiniJson.GetString(k, "holderId"), HolderName = MiniJson.GetString(k, "holderName"),
                    TopicKey = MiniJson.GetString(k, "topic"), Summary = MiniJson.GetString(k, "summary"),
                    Source = MiniJson.GetString(k, "source"), ConfidenceWhenLearned = Num(k, "conf"),
                    LearnedAt = GameTime.FromTotalMinutes((long)Num(k, "learnedAt")),
                    Sensitive = Flag(k, "sensitive"), Handled = Flag(k, "handled"),
                });
            }

            foreach (var o in MiniJson.GetList(root, "secrets") ?? new List<object>())
            {
                var s = MiniJson.AsObject(o);
                var secret = s != null ? secrets.ById(MiniJson.GetString(s, "id")) : null;
                if (secret == null) continue;
                secret.Restore(Flag(s, "known"), Flag(s, "spent"), MiniJson.GetString(s, "from"),
                    GameTime.FromTotalMinutes((long)Num(s, "learnedAt")));
            }

            foreach (var o in MiniJson.GetList(root, "beats") ?? new List<object>())
            {
                var b = MiniJson.AsObject(o);
                if (b == null) continue;
                var beat = beats.All.FirstOrDefault(x => x.Id == MiniJson.GetString(b, "id"));
                if (beat != null && Enum.TryParse(MiniJson.GetString(b, "state"), out BeatState bs))
                    beat.Restore(bs);
            }

            foreach (var o in MiniJson.GetList(root, "debts") ?? new List<object>())
            {
                var dd = MiniJson.AsObject(o);
                var debtor = dd != null && debts != null ? debts.ById(MiniJson.GetString(dd, "id")) : null;
                if (debtor != null)
                    debtor.Restore(Flag(dd, "collected"), Flag(dd, "forgiven"), MiniJson.GetInt(dd, "lastAskedDay"));
            }

            mill.RestoreDiscredited((MiniJson.GetList(root, "discredited") ?? new List<object>()).OfType<string>());
            foreach (var o in MiniJson.GetList(root, "agents") ?? new List<object>())
            {
                var a = MiniJson.AsObject(o);
                var g = a != null ? mill.Get(MiniJson.GetString(a, "id")) : null;
                if (g == null) continue;
                g.Loyalty = Num(a, "loyalty");
                g.Leashed = Flag(a, "leashed");
                g.Suspicion.Restore(Num(a, "suspicion"));
                g.Suppressed.Clear();
                foreach (var t in (MiniJson.GetList(a, "suppressed") ?? new List<object>()).OfType<string>())
                    g.Suppressed.Add(t);
                g.Rumors.Clear();
                foreach (var ro in MiniJson.GetList(a, "rumors") ?? new List<object>())
                {
                    var r = MiniJson.AsObject(ro);
                    if (r == null) continue;
                    g.Rumors.Add(new Rumor
                    {
                        Content = new Fact(MiniJson.GetString(r, "subj"), MiniJson.GetString(r, "pred"), MiniJson.GetString(r, "val")),
                        OriginId = MiniJson.GetString(r, "origin"), Summary = MiniJson.GetString(r, "summary"),
                        Confidence = Num(r, "conf"), Hops = MiniJson.GetInt(r, "hops"), Sensitive = Flag(r, "sensitive"),
                    });
                }
                g.Knowledge.Facts.Clear();
                foreach (var fo in MiniJson.GetList(a, "facts") ?? new List<object>())
                {
                    var f = MiniJson.AsObject(fo);
                    if (f == null) continue;
                    g.Knowledge.Learn(new Fact(MiniJson.GetString(f, "subj"), MiniJson.GetString(f, "pred"), MiniJson.GetString(f, "val")));
                }
            }
            return now;
        }

        static double Num(Dictionary<string, object> obj, string key) =>
            obj != null && obj.TryGetValue(key, out var v) && v != null ? Convert.ToDouble(v) : 0.0;

        static bool Flag(Dictionary<string, object> obj, string key) =>
            obj != null && obj.TryGetValue(key, out var v) && v is bool b && b;
    }
}
