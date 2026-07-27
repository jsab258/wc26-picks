using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// The consequence layer of violence (roadmap M11).
    ///
    /// The player deferred playable melee — correctly, since positioning-and-
    /// timing combat cannot be judged on capsules and needs the art pass. But
    /// the design doc's line about violence is not about the fighting: *injuries
    /// persist, crew members carry trauma, and every fight happened in front of
    /// somebody who remembers it.* None of that needs a brawling system. All of
    /// it needs to exist BEFORE one, because a punch with no aftermath teaches
    /// the player that violence is free, and that lesson is very hard to take
    /// back later.
    ///
    /// So this is the half that can land now: harm that lasts, costs, shows, and
    /// is remembered. Violence enters through the systems that already exist —
    /// an operation that goes wrong, a rival's answer, the Fall — rather than
    /// through a fight the player controls.
    ///
    /// THE RULE THAT SHAPES EVERYTHING HERE: an injury is information. It is on
    /// your face, the infirmary keeps hours and neighbours, and a man with his
    /// hand wrapped on Tuesday cannot claim he was somewhere quiet on Monday
    /// night. Getting hurt does not merely cost you capability; it costs you
    /// the ability to have been elsewhere.

    public enum InjuryKind
    {
        /// A day or two, and it shows. Everyone can see you were in something.
        Bruised,
        /// Bleeds, scars, and turns bad if nobody looks at it.
        Cut,
        /// Weeks. You cannot do the work.
        Broken,
        /// The kind people speak about in the past tense until you turn up.
        Bad,
    }

    public class Injury
    {
        public string PersonId;
        public string PersonName;
        public InjuryKind Kind;
        public int DayTaken;
        public int HealsOnDay;
        /// What a witness would say happened, in a person's words. Never a
        /// mechanism — "somebody put him through the rail at the ferry", not
        /// "melee_impact_heavy".
        public string Cause;
        public bool Treated;
        /// Untreated wounds go bad. Set once, so a wound cannot rot twice.
        public bool WentBad;
        /// Whether it is on show. A cracked rib is nobody's business; a face is.
        public bool Visible;

        public bool HealedBy(int day) => day >= HealsOnDay;

        /// 0..1. How much of a person this injury takes away.
        public double Severity =>
            Kind == InjuryKind.Bruised ? 0.15 :
            Kind == InjuryKind.Cut ? 0.30 :
            Kind == InjuryKind.Broken ? 0.60 : 0.85;

        /// How it reads to somebody looking at them.
        public string Look =>
            Kind == InjuryKind.Bruised ? "marked up, one eye going purple"
            : Kind == InjuryKind.Cut ? "a dressing on the forearm, and favouring it"
            : Kind == InjuryKind.Broken ? "strapped, moving like an old man"
            : "grey, and not standing on his own";
    }

    /// Two people who have hurt each other, and have not stopped.
    ///
    /// Modelled as a first-class thing rather than as suspicion, because a feud
    /// is not a belief — it does not decay when you leave the room, it is not
    /// about what somebody thinks happened, and it does not get resolved by
    /// evidence. It gets resolved by somebody choosing to stop.
    public class Feud
    {
        public string AId, BId;
        public string AName, BName;
        /// 0..1. Falls slowly. Rises every time either of them acts on it.
        public double Heat;
        public int StartedDay;
        public int LastFlaredDay = -1;
        public bool Settled;
        /// How many times it has gone round. The Director reads this: a feud on
        /// its fourth exchange is a different story from a fresh one.
        public int Exchanges;

        public bool Involves(string id) => !Settled && (AId == id || BId == id);
        public string Other(string id) => AId == id ? BId : AId;
    }

    public class HarmBook
    {
        /// Untreated wounds turn. This is the number that makes the infirmary a
        /// decision rather than a formality.
        public const int DaysBeforeItTurns = 2;
        /// Treatment prices, in the only currency that matters here: clean money
        /// and being seen paying it.
        public static int PriceOf(InjuryKind kind) =>
            kind == InjuryKind.Bruised ? 15 :
            kind == InjuryKind.Cut ? 45 :
            kind == InjuryKind.Broken ? 140 : 320;

        static int DaysToHeal(InjuryKind kind, bool treated) =>
            kind == InjuryKind.Bruised ? (treated ? 1 : 3)
            : kind == InjuryKind.Cut ? (treated ? 3 : 7)
            : kind == InjuryKind.Broken ? (treated ? 12 : 25)
            : (treated ? 21 : 45);

        readonly List<Injury> _injuries = new List<Injury>();
        readonly List<Feud> _feuds = new List<Feud>();
        readonly Dictionary<string, int> _scars = new Dictionary<string, int>();

        public IReadOnlyList<Injury> All => _injuries;
        public IReadOnlyList<Feud> Feuds => _feuds;

        /// How many times this person has been hurt, ever. Trauma is cumulative
        /// and does not heal with the wound — that is the whole difference
        /// between an injury and a scar.
        public int ScarsOf(string id) => _scars.TryGetValue(id, out var n) ? n : 0;

        // ---- getting hurt ----

        /// Somebody got hurt. Returns the injury so the caller can narrate it;
        /// the caller owns the witnesses, because who saw it is a gossip
        /// question and this file does not know where anybody was standing.
        public Injury Inflict(string personId, string personName, InjuryKind kind, int day,
            string cause, bool visible = true)
        {
            if (string.IsNullOrEmpty(personId)) return null;
            var injury = new Injury
            {
                PersonId = personId,
                PersonName = personName ?? personId,
                Kind = kind,
                DayTaken = day,
                HealsOnDay = day + DaysToHeal(kind, false),
                Cause = cause,
                Visible = visible,
            };
            _injuries.Add(injury);
            _scars[personId] = ScarsOf(personId) + 1;
            return injury;
        }

        /// Everything currently wrong with somebody.
        public List<Injury> Hurts(string personId, int day)
        {
            var list = new List<Injury>();
            foreach (var i in _injuries)
                if (i.PersonId == personId && !i.HealedBy(day)) list.Add(i);
            return list;
        }

        public bool IsHurt(string personId, int day) => Hurts(personId, day).Count > 0;

        /// 0..1, what fraction of themselves this person currently is. Injuries
        /// compound rather than add — three bruises are not a broken arm — so
        /// they multiply, which also means capability can never go negative and
        /// a person is never quite nothing.
        public double Capability(string personId, int day)
        {
            double c = 1.0;
            foreach (var i in Hurts(personId, day)) c *= 1.0 - i.Severity;
            return Math.Max(0.05, c);
        }

        /// What somebody looking at them would say, or null if they look fine.
        /// The worst visible thing wins — you notice the eye before the limp.
        public string LooksLike(string personId, int day)
        {
            Injury worst = null;
            foreach (var i in Hurts(personId, day))
                if (i.Visible && (worst == null || i.Severity > worst.Severity)) worst = i;
            return worst?.Look;
        }

        // ---- the infirmary ----

        /// Pay to have it looked at. Heals faster and cannot turn bad.
        ///
        /// The cost is not only the money. Treatment is a PLACE with hours and
        /// neighbours, so the caller plants the fact that you were there — and
        /// a man whose hand was dressed on Tuesday cannot have been somewhere
        /// quiet on Monday night. Returns what it cost, or 0 if it did not
        /// happen (already treated, healed, or the money was not there).
        public int Treat(Injury injury, Wallet wallet, int day)
        {
            if (injury == null || injury.Treated || injury.HealedBy(day)) return 0;
            int price = PriceOf(injury.Kind);
            // Clean money only. You cannot hand a doctor a roll of night money
            // and expect the visit not to be remembered for the wrong reason.
            if (wallet != null && !wallet.Spend(price, dirtyOk: false)) return 0;
            injury.Treated = true;
            // Healing restarts from today, not from the day it happened: a week
            // of ignoring it does not count as a week of getting better.
            injury.HealsOnDay = day + DaysToHeal(injury.Kind, true);
            return price;
        }

        /// The day passes. Untreated wounds that have been left long enough turn
        /// bad — longer, worse, and no longer something you can walk off.
        /// Returns what a person would say about each change.
        public List<string> DailyTick(int day)
        {
            var news = new List<string>();
            foreach (var i in _injuries)
            {
                if (i.Treated || i.WentBad || i.HealedBy(day)) continue;
                if (day - i.DayTaken < DaysBeforeItTurns) continue;
                if (i.Kind == InjuryKind.Bruised) continue;   // a bruise is just a bruise

                i.WentBad = true;
                i.HealsOnDay += DaysToHeal(i.Kind, false) / 2;
                if (i.Kind == InjuryKind.Cut) i.Kind = InjuryKind.Broken;
                else i.Kind = InjuryKind.Bad;
                news.Add($"{i.PersonName} left it too long. It has gone bad, and now it is the kind of thing people ask about.");
            }

            // Feuds cool, but slowly, and never on their own to nothing — the
            // last of it is settled by somebody, not by time.
            foreach (var f in _feuds)
            {
                if (f.Settled) continue;
                f.Heat = Math.Max(0.2, f.Heat - 0.03);
            }
            return news;
        }

        // ---- feuds ----

        public Feud FeudBetween(string a, string b)
        {
            foreach (var f in _feuds)
            {
                if (f.Settled) continue;
                if ((f.AId == a && f.BId == b) || (f.AId == b && f.BId == a)) return f;
            }
            return null;
        }

        /// A hurt somebody, and it is not over. Idempotent by pair: a second
        /// exchange flares the same feud rather than starting a rival one, so
        /// two people can never be in two feuds with each other.
        public Feud Flare(string aId, string aName, string bId, string bName, int day, double heat = 0.35)
        {
            if (string.IsNullOrEmpty(aId) || string.IsNullOrEmpty(bId) || aId == bId) return null;
            var f = FeudBetween(aId, bId);
            if (f == null)
            {
                f = new Feud
                {
                    AId = aId, BId = bId, AName = aName ?? aId, BName = bName ?? bId,
                    StartedDay = day, Heat = Math.Clamp(heat, 0, 1),
                };
                _feuds.Add(f);
            }
            else
            {
                f.Heat = Math.Clamp(f.Heat + heat, 0, 1);
            }
            if (f.LastFlaredDay != day) f.Exchanges++;
            f.LastFlaredDay = day;
            return f;
        }

        /// Somebody chose to stop. That is the only way a feud ends, which is
        /// why it is worth having as a thing the player can spend on.
        public bool Settle(Feud f)
        {
            if (f == null || f.Settled) return false;
            f.Settled = true;
            f.Heat = 0;
            return true;
        }

        /// Everyone this person is at odds with right now.
        public List<Feud> FeudsOf(string id)
        {
            var list = new List<Feud>();
            foreach (var f in _feuds) if (f.Involves(id)) list.Add(f);
            return list;
        }

        /// Will these two work together? A feud past a certain heat means no,
        /// and that is a scheduling problem the player has to solve with people
        /// rather than with a menu.
        public bool WillWorkTogether(string a, string b)
        {
            var f = FeudBetween(a, b);
            return f == null || f.Heat < 0.5;
        }

        /// The hottest unsettled feud, for the Director to read. Nothing here
        /// decides anything; it reports, and the game decides.
        public Feud Hottest()
        {
            Feud best = null;
            foreach (var f in _feuds)
                if (!f.Settled && (best == null || f.Heat > best.Heat)) best = f;
            return best;
        }

        // ---- persistence ----

        public Dictionary<string, object> Capture()
        {
            var injuries = new List<object>();
            foreach (var i in _injuries)
                injuries.Add(new Dictionary<string, object>
                {
                    { "id", i.PersonId }, { "name", i.PersonName }, { "kind", i.Kind.ToString() },
                    { "day", i.DayTaken }, { "heals", i.HealsOnDay }, { "cause", i.Cause ?? "" },
                    { "treated", i.Treated }, { "wentBad", i.WentBad }, { "visible", i.Visible },
                });
            var feuds = new List<object>();
            foreach (var f in _feuds)
                feuds.Add(new Dictionary<string, object>
                {
                    { "a", f.AId }, { "b", f.BId }, { "aName", f.AName }, { "bName", f.BName },
                    { "heat", Math.Round(f.Heat, 4) }, { "started", f.StartedDay },
                    { "flared", f.LastFlaredDay }, { "settled", f.Settled }, { "exchanges", f.Exchanges },
                });
            var scars = new List<object>();
            foreach (var pair in _scars)
                scars.Add(new Dictionary<string, object> { { "id", pair.Key }, { "n", pair.Value } });
            return new Dictionary<string, object>
            {
                { "injuries", injuries }, { "feuds", feuds }, { "scars", scars },
            };
        }

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            var il = MiniJson.GetList(data, "injuries");
            if (il != null)
            {
                _injuries.Clear();
                foreach (var raw in il)
                {
                    var o = MiniJson.AsObject(raw);
                    if (o == null) continue;
                    _injuries.Add(new Injury
                    {
                        PersonId = MiniJson.GetString(o, "id"),
                        PersonName = MiniJson.GetString(o, "name"),
                        Kind = ParseKind(MiniJson.GetString(o, "kind")),
                        DayTaken = MiniJson.GetInt(o, "day"),
                        HealsOnDay = MiniJson.GetInt(o, "heals"),
                        Cause = MiniJson.GetString(o, "cause"),
                        Treated = Flag(o, "treated"),
                        WentBad = Flag(o, "wentBad"),
                        Visible = Flag(o, "visible"),
                    });
                }
            }
            var fl = MiniJson.GetList(data, "feuds");
            if (fl != null)
            {
                _feuds.Clear();
                foreach (var raw in fl)
                {
                    var o = MiniJson.AsObject(raw);
                    if (o == null) continue;
                    _feuds.Add(new Feud
                    {
                        AId = MiniJson.GetString(o, "a"), BId = MiniJson.GetString(o, "b"),
                        AName = MiniJson.GetString(o, "aName"), BName = MiniJson.GetString(o, "bName"),
                        Heat = Num(o, "heat"), StartedDay = MiniJson.GetInt(o, "started"),
                        LastFlaredDay = MiniJson.GetInt(o, "flared"),
                        Settled = Flag(o, "settled"), Exchanges = MiniJson.GetInt(o, "exchanges"),
                    });
                }
            }
            var sl = MiniJson.GetList(data, "scars");
            if (sl != null)
            {
                _scars.Clear();
                foreach (var raw in sl)
                {
                    var o = MiniJson.AsObject(raw);
                    var id = MiniJson.GetString(o, "id");
                    if (!string.IsNullOrEmpty(id)) _scars[id] = MiniJson.GetInt(o, "n");
                }
            }
        }

        static bool Flag(Dictionary<string, object> o, string key) =>
            o != null && o.TryGetValue(key, out var v) && v is bool b && b;

        static double Num(Dictionary<string, object> o, string key) =>
            o != null && o.TryGetValue(key, out var v) && v is double d ? d : 0;

        static InjuryKind ParseKind(string s) =>
            s == "Cut" ? InjuryKind.Cut :
            s == "Broken" ? InjuryKind.Broken :
            s == "Bad" ? InjuryKind.Bad : InjuryKind.Bruised;
    }
}
