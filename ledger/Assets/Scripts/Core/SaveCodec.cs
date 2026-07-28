using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// P5: consequences persist — the city's state IS the save file. The codec
    /// overlays state onto freshly-authored objects (cards, beats, secrets and
    /// gossipers are rebuilt by the bootstrap; the save carries only what play
    /// changed). NPC memories persist separately as markdown and are not here.
    /// Why a save can't be read: the reason the front end shows the player.
    public enum SaveFault { None, Unreadable, FromTheFuture }

    public class SaveIncompatibleException : Exception
    {
        public SaveFault Fault { get; }
        public SaveIncompatibleException(SaveFault fault, string message) : base(message) => Fault = fault;
    }

    public static class SaveCodec
    {
        /// Bump when a change would make an OLD save restore WRONGLY rather
        /// than merely incompletely. Additive fields never need a bump: the
        /// codec skips unknown ids and defaults missing keys, so v1 saves load
        /// into v2 worlds unharmed. Migrate() carries the rest forward.
        public const int Version = 2;

        /// The oldest save this build can still read.
        public const int MinReadableVersion = 1;

        /// A save's version without committing to loading it — the front end
        /// uses this to decide whether "Continue" is offered at all.
        public static int PeekVersion(string json)
        {
            try
            {
                var root = MiniJson.AsObject(MiniJson.Deserialize(json));
                return root == null ? 0 : MiniJson.GetInt(root, "version");
            }
            catch (Exception) { return 0; }
        }

        /// Bring an older save's shape forward. Each step is small and named,
        /// so a v1 file from the first playtest still opens in a v9 build.
        static void Migrate(Dictionary<string, object> root, int from)
        {
            if (from < 2)
            {
                // v1 -> v2: the open city, the empire, the day job and Act II
                // arrived as additive keys. A v1 save is a week-mode save by
                // definition; make that explicit rather than leaving it implied.
                if (!root.ContainsKey("openMode")) root["openMode"] = false;
                if (!root.ContainsKey("falls")) root["falls"] = 0;
            }
        }

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
                { "openMode", camp.OpenMode }, { "outfitCutOff", camp.OutfitCutOff },
                { "fallPending", camp.FallPending }, { "falls", camp.Falls },
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

            // Full authored fields ride along so a beat the RUNTIME generated
            // (the open city's evening_dN invitations) can be rebuilt on load —
            // id+state alone restored only beats the fresh boot re-authors,
            // silently dropping every generated evening (audit 2026-07-27).
            root["beats"] = beats.All.Select(b => (object)new Dictionary<string, object>
            {
                { "id", b.Id }, { "state", b.State.ToString() },
                { "host", b.HostId }, { "title", b.Title }, { "day", b.Day },
                { "from", b.StartHour }, { "to", b.EndHour }, { "invite", b.InviteText ?? "" },
            }).ToList();

            root["debts"] = (debts != null ? debts.All : Enumerable.Empty<Debtor>())
                .Select(d => (object)new Dictionary<string, object>
                {
                    { "id", d.Id }, { "collected", d.Collected }, { "forgiven", d.Forgiven },
                    { "lastAskedDay", d.LastAskedDay },
                    // The remaining balance, because part-payment changes it and
                    // a debt that reset to its original figure on load would be
                    // a quiet way of stealing back what the player collected.
                    { "amount", d.Amount },
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
            Dictionary<string, object> root;
            try { root = MiniJson.AsObject(MiniJson.Deserialize(json)); }
            catch (Exception e) { throw new SaveIncompatibleException(SaveFault.Unreadable, e.Message); }
            if (root == null) throw new SaveIncompatibleException(SaveFault.Unreadable, "save file unreadable");

            int saved = MiniJson.GetInt(root, "version");
            if (saved > Version)
                throw new SaveIncompatibleException(SaveFault.FromTheFuture,
                    $"this save was written by a newer build (v{saved}; this build reads v{Version})");
            if (saved < MinReadableVersion)
                throw new SaveIncompatibleException(SaveFault.Unreadable,
                    $"save version v{saved} is older than this build can read (v{MinReadableVersion})");
            if (saved < Version) Migrate(root, saved);

            extra = MiniJson.GetObject(root, "extra") ?? new Dictionary<string, object>();

            var now = new GameTime(MiniJson.GetInt(root, "day"), MiniJson.GetInt(root, "hour"), MiniJson.GetInt(root, "minute"));
            wallet.Restore(MiniJson.GetInt(root, "clean"), MiniJson.GetInt(root, "dirty"), MiniJson.GetInt(root, "washed"));

            Enum.TryParse(MiniJson.GetString(root, "verdict"), out Verdict verdict);
            camp.Restore(Num(root, "patience"), MiniJson.GetInt(root, "exposedStreak"),
                MiniJson.GetInt(root, "jobsDone"), MiniJson.GetInt(root, "jobsMissed"),
                MiniJson.GetInt(root, "daysClosed"), verdict, MiniJson.GetString(root, "verdictReason"));
            camp.RestoreOpen(Flag(root, "openMode"), Flag(root, "outfitCutOff"),
                Flag(root, "fallPending"), MiniJson.GetInt(root, "falls"));

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
                if (beat == null && b.ContainsKey("day"))
                {
                    beat = new Beat
                    {
                        Id = MiniJson.GetString(b, "id"), HostId = MiniJson.GetString(b, "host"),
                        Title = MiniJson.GetString(b, "title"), Day = MiniJson.GetInt(b, "day"),
                        StartHour = MiniJson.GetInt(b, "from"), EndHour = MiniJson.GetInt(b, "to"),
                        InviteText = MiniJson.GetString(b, "invite"),
                    };
                    beats.Add(beat);
                }
                if (beat != null && Enum.TryParse(MiniJson.GetString(b, "state"), out BeatState bs))
                    beat.Restore(bs);
            }

            foreach (var o in MiniJson.GetList(root, "debts") ?? new List<object>())
            {
                var dd = MiniJson.AsObject(o);
                var debtor = dd != null && debts != null ? debts.ById(MiniJson.GetString(dd, "id")) : null;
                if (debtor != null)
                    debtor.Restore(Flag(dd, "collected"), Flag(dd, "forgiven"), MiniJson.GetInt(dd, "lastAskedDay"),
                        dd.ContainsKey("amount") ? MiniJson.GetInt(dd, "amount") : -1);
            }

            mill.RestoreDiscredited((MiniJson.GetList(root, "discredited") ?? new List<object>()).OfType<string>());
            RestoreAgents(root, mill);
            return now;
        }

        /// Re-applies saved agent state onto whichever agents EXIST in the mill
        /// right now. Public because restore is two-pass: the main Restore runs
        /// before the population layer has promoted crowd residents back into
        /// the mill, so a promoted resident's saved rumors, loyalty, suspicion
        /// and leash were silently dropped along with the unknown id (audit
        /// 2026-07-27). Call this again once every agent exists; re-applying to
        /// an agent that was already restored is harmless — the same state
        /// lands twice.
        public static void RestoreMillAgents(string json, GossipMill mill)
        {
            Dictionary<string, object> root;
            try { root = MiniJson.AsObject(MiniJson.Deserialize(json)); }
            catch { return; }
            if (root == null) return;
            RestoreAgents(root, mill);
        }

        static void RestoreAgents(Dictionary<string, object> root, GossipMill mill)
        {
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
        }

        static double Num(Dictionary<string, object> obj, string key) =>
            obj != null && obj.TryGetValue(key, out var v) && v != null ? Convert.ToDouble(v) : 0.0;

        static bool Flag(Dictionary<string, object> obj, string key) =>
            obj != null && obj.TryGetValue(key, out var v) && v is bool b && b;
    }
}
