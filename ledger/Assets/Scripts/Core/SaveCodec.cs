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

        /// A day number beyond which the file is corrupt rather than long.
        ///
        /// NOT A GAME RULE AND NOT A GUESS. Open city has no ending and nobody
        /// is capping how long a campaign runs. This exists because the day
        /// counter is an `int` that `GameController` uses as a loop induction
        /// variable — `for (int day = from; day &lt;= Now.Day; day++)`, catching
        /// the world up over days the Fall skipped — and at `int.MaxValue` the
        /// increment wraps to `int.MinValue` and the condition is true again.
        /// The loop cannot terminate. `SaveChaos` restored exactly that world
        /// from a save carrying `"day": 9223372036854775807`.
        ///
        /// So the bound is derived from the arithmetic rather than from taste,
        /// and it is set far below the failure — 100,000 in-game days is 274
        /// years of play, four orders of magnitude short of the overflow and
        /// unreachable by any human. Anything past it did not come from
        /// playing; it came from a corrupt file, and refusing it here is what
        /// keeps that loop reachable only by real days.
        public const int MaxPlayableDay = 100000;

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
                // WHICH nights, not just how many — the competence axis reads
                // a list and a total cannot tell one bad week from six in a row.
                { "missedNights", camp.MissedNights.Select(n => (object)n).ToList() },
                { "doneNights", camp.DoneNights.Select(n => (object)n).ToList() },
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
                        { "hops", r.Hops }, { "sensitive", r.Sensitive }, { "indelible", r.Indelible },
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

            // THE DAY IS REQUIRED, and it is the only key here that is.
            //
            // Everything else in a save has a defensible default — no debts is
            // no debts, no beats is no beats — so `GetInt`'s "0 for absent" is
            // right for them and catastrophic for this one. `SaveChaos` deleted
            // the `day` key and the save LOADED, into day 0, which is outside
            // the range every schedule, beat, gossip decay and campaign check in
            // the game assumes without testing. It would have failed days later,
            // elsewhere, looking like a simulation bug.
            //
            // Refused rather than clamped to 1. A file that quietly rewinds the
            // player's week to its first morning is a worse outcome than one
            // that says it cannot be read, because only the second is a thing
            // the player can act on — and the front end already has the screen
            // for it.
            if (!MiniJson.TryGetInt(root, "day", out int day) || day < 1 || day > MaxPlayableDay)
                throw new SaveIncompatibleException(SaveFault.Unreadable,
                    "the save has no readable day — it is truncated or corrupt");

            // AND THE CLOCK, checked here rather than inside `GameTime`.
            //
            // `GameTime` is a plain struct that every system in the game
            // constructs from values it computed itself, and teaching it to
            // normalise would change behaviour for a hundred trusted callers to
            // defend against one untrusted one. The codec is the trust
            // boundary; this is where a number stops being data and starts
            // being state.
            //
            // A MISSING hour defaults to zero, because midnight is a real time
            // and an absent key is an old save. A PRESENT hour of 2,147,483,647
            // is not a time, and `SaveChaos` restored one — clamping it would
            // have moved the player's clock by up to a day without telling
            // them, so a clock that is present and impossible refuses.
            int hour = MiniJson.GetInt(root, "hour"), minute = MiniJson.GetInt(root, "minute");
            if (hour < 0 || hour > 23 || minute < 0 || minute > 59)
                throw new SaveIncompatibleException(SaveFault.Unreadable,
                    $"the save's clock reads {hour:00}:{minute:00}, which is not a time");
            var now = new GameTime(day, hour, minute);
            wallet.Restore(MiniJson.GetInt(root, "clean"), MiniJson.GetInt(root, "dirty"), MiniJson.GetInt(root, "washed"));

            Enum.TryParse(MiniJson.GetString(root, "verdict"), out Verdict verdict);
            camp.Restore(Num(root, "patience"), MiniJson.GetInt(root, "exposedStreak"),
                MiniJson.GetInt(root, "jobsDone"), MiniJson.GetInt(root, "jobsMissed"),
                MiniJson.GetInt(root, "daysClosed"), verdict, MiniJson.GetString(root, "verdictReason"));
            camp.RestoreNights(MiniJson.GetList(root, "missedNights"),
                               MiniJson.GetList(root, "doneNights"));
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
                    // A RUMOUR THAT LOST ITS SUBJECT IS NOT A RUMOUR. `Fact`
                    // refuses null now rather than dereferencing it, so this
                    // has to be the place the decision is made — and the
                    // decision is to drop the record, which is what the codec
                    // already does for an unknown secret id, an unparseable
                    // beat and a null object. It was simply never done here,
                    // and `SaveChaos` found it by deleting one key.
                    var content = FactOrNull(r);
                    if (content == null) continue;
                    g.Rumors.Add(new Rumor
                    {
                        Content = content,
                        OriginId = MiniJson.GetString(r, "origin"), Summary = MiniJson.GetString(r, "summary"),
                        Confidence = Num(r, "conf"), Hops = MiniJson.GetInt(r, "hops"), Sensitive = Flag(r, "sensitive"),
                        Indelible = Flag(r, "indelible"),
                    });
                }
                g.Knowledge.Facts.Clear();
                foreach (var fo in MiniJson.GetList(a, "facts") ?? new List<object>())
                {
                    var f = MiniJson.AsObject(fo);
                    if (f == null) continue;
                    var fact = FactOrNull(f);
                    if (fact != null) g.Knowledge.Learn(fact);
                }
            }
        }

        /// A `Fact` from a saved record, or null if the record cannot make one.
        ///
        /// The three parts are all load-bearing — `SameTopic` compares subject
        /// and predicate, so a fact missing either would match things it has
        /// nothing to do with and contradict them. Dropping it loses one
        /// rumour; keeping it corrupts the contradiction check the whole lying
        /// system runs on.
        static Fact FactOrNull(Dictionary<string, object> rec)
        {
            var subj = MiniJson.GetString(rec, "subj");
            var pred = MiniJson.GetString(rec, "pred");
            var val = MiniJson.GetString(rec, "val");
            if (subj == null || pred == null || val == null) return null;
            return new Fact(subj, pred, val);
        }

        static double Num(Dictionary<string, object> obj, string key) =>
            obj != null && obj.TryGetValue(key, out var v) && v != null ? Convert.ToDouble(v) : 0.0;

        static bool Flag(Dictionary<string, object> obj, string key) =>
            obj != null && obj.TryGetValue(key, out var v) && v is bool b && b;
    }
}
