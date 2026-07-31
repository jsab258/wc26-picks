using System.Collections.Generic;
using System.Linq;
using Ledger.Core;
using UnityEngine;

namespace Ledger.Game
{
    /// The game-side half of the Director (roadmap M8, design doc §17 gap 2).
    /// Two jobs, mirroring the router's bridge exactly:
    ///
    ///  1. BUILD THE SNAPSHOT the Director is allowed to read — assembled from
    ///     live state, and nothing else reaches the model. Crucially it includes
    ///     what the player has LEFT UNDONE, because that is where honest pressure
    ///     comes from. A world that generates misfortune out of nowhere is a
    ///     random event table wearing a simulation's coat.
    ///
    ///  2. FIRE a due pressure through the primitives the game already has. The
    ///     Director scheduled an occasion; this runs it the same way an authored
    ///     beat is run. It cannot reach anything a pressure kind does not name.
    ///
    /// What the player is never shown: the pending list. Pillar §6.2 says the
    /// player sees what they believe, never ground truth — a UI panel reading
    /// "a demand from Mitch is coming on day 14" would undo the entire game.
    public partial class GameController
    {
        public DirectorBook Directorate { get; } = new DirectorBook();
        Director _director;
        int _lastDirectorDay = -1;

        Director TheDirector => _director ?? (_director = new Director(Llm, Cost));

        /// Outstanding demands the Director has made: who wants how much, by when.
        /// A real obligation with a real window, exactly like the outfit's drops.
        public class OpenDemand
        {
            public string Who;
            public int Amount;
            public int DueDay;
            public string Line;
        }
        public readonly List<OpenDemand> Demands = new List<OpenDemand>();

        public OpenDemand DemandFrom(string who) =>
            Demands.FirstOrDefault(d => d.Who == who);

        // ---------------------------------------------------------------
        // 1. The snapshot
        // ---------------------------------------------------------------

        WorldSnapshot BuildWorldSnapshot()
        {
            var w = new WorldSnapshot
            {
                Day = Now.Day,
                Heat = CurrentHeat,
                Street = $"{Economy.ProsperityWord()}, prices {Economy.PriceWord()}",
            };

            var mill = _gossip != null ? _gossip.Mill : null;
            if (mill == null) return w;

            // Everybody the player could actually run into, with how they feel
            // and one line of why it might matter tonight.
            foreach (var host in _hosts)
            {
                if (host == null || host.Card == null) continue;
                var name = host.Card.Name;
                var g = mill.Get(name);
                w.People.Add(new WorldPerson(
                    name,
                    RoleOf(name),
                    g != null ? g.Loyalty : 0.5,
                    host.Suspicion != null ? host.Suspicion.Value : 0.0,
                    NoteOn(name)));
            }

            // What has been left undone. The richest and most honest source of
            // pressure in the whole game.
            foreach (var s in Economy.Suppliers)
            {
                if (s.Refusing) w.Ignored.Add($"{s.Name} has stopped bringing {s.Goods} and has not been made right with");
                else if (s.Unpaid > 0) w.Ignored.Add($"{s.Name} is owed for {s.Unpaid} deliveries of {s.Goods}");
            }
            foreach (var c in Empire.ActiveCrew)
                if (c.Cut == "skim") w.Ignored.Add($"{c.Name} has been on a skimmed cut since day {c.RecruitedDay}");
            foreach (var d in Debts.All)
                if (d.Outstanding) w.Ignored.Add($"{d.Name} still owes Mickey's book £{d.Amount}");
            int unhandled = Knowledge.Entries.Count(k => !k.Handled);
            if (unhandled > 0) w.Ignored.Add($"{unhandled} stories about the player are in the street and unanswered");
            foreach (var d in Demands)
                w.Ignored.Add($"{d.Who} asked for £{d.Amount} by day {d.DueDay} and has not had it");

            // What just happened.
            if (LastTakings >= 0) w.Recent.Add($"the bar took £{LastTakings} yesterday");
            if (Empire.TotalRacketIncome > 0) w.Recent.Add($"the rounds have brought in £{Empire.TotalRacketIncome} in total");
            foreach (var a in Empire.Arms)
                if (a.Stage > 0) w.Recent.Add($"{a.HeadName}'s people are at stage {a.Stage} of taking an interest");
            foreach (var line in Directorate.History.Skip(System.Math.Max(0, Directorate.History.Count - 3)))
                w.Recent.Add(line);

            w.InFlight.AddRange(Directorate.InFlightLines());
            return w;
        }

        string RoleOf(string name)
        {
            if (name == "Lena") return "bookkeeper, keeps the bar's books";
            if (Empire.Arms.Any(a => a.HeadName == name)) return "head of a rival organization";
            if (Empire.CrewOf(name) != null) return "works for the player";
            if (Economy.Suppliers.Any(s => s.Name == name)) return "supplier";
            if (Empire.Businesses.Any(b => b.OwnerId == name)) return "runs a business on this street";
            if (name == "Mara Ellis") return "police detective working a case on this street";
            return "lives or works on this street";
        }

        string NoteOn(string name)
        {
            var s = Economy.Suppliers.FirstOrDefault(x => x.Name == name);
            if (s != null && s.Refusing) return $"has stopped delivering {s.Goods}";
            if (s != null && s.Unpaid > 0) return $"owed for {s.Unpaid} deliveries";
            var crew = Empire.CrewOf(name);
            if (crew != null && crew.Cut == "skim") return "has been skimmed on every envelope";
            if (crew != null && crew.Cut == "generous") return "has been paid better than the work is worth";
            var debt = Debts.Of(name);
            if (debt != null && debt.Outstanding) return $"owes the book £{debt.Amount}";
            var biz = Empire.Businesses.FirstOrDefault(b => b.OwnerId == name && b.Owned);
            if (biz != null) return $"lost the {biz.Name} to the player and still runs the counter";
            return null;
        }

        // ---------------------------------------------------------------
        // 2. The nightly pass
        // ---------------------------------------------------------------

        /// Called once at the daily close. Cheap when it declines, which is most
        /// nights: ShouldRun is deterministic and runs before any call is made.
        async void RunDirectorAsync()
        {
            // The WHOLE body is guarded, not just the call. This is an async void
            // on the daily-close path: anything that escapes it is an unhandled
            // exception with no caller to catch it, which in this game means a
            // red build and, worse, a morning that does not happen. Building the
            // snapshot touches a dozen systems and the key file; none of that is
            // worth a crash when the correct fallback is simply a quiet night.
            try
            {
                var world = BuildWorldSnapshot();
                if (!TheDirector.ShouldRun(world, _lastDirectorDay)) return;
                _lastDirectorDay = Now.Day;
                Directorate.LastRunDay = Now.Day;

                var p = await TheDirector.ProposeAsync(world);
                if (p == null || !p.IsSomething) return;
                Directorate.Schedule(p);
            }
            catch (System.Exception e)
            {
                Debug.LogWarning($"Director: quiet night ({e.GetType().Name}).");
            }
        }

        // ---------------------------------------------------------------
        // 3. Firing
        // ---------------------------------------------------------------

        /// Runs whatever the Director scheduled for today, through the game's
        /// existing primitives and nothing else.
        void FireDuePressures()
        {
            foreach (var p in Directorate.Due(Now))
            {
                if (!Fire(p)) continue;
                Directorate.History.Add(p.Line);
                _ui?.Toast(p.Line, 12f);
                Audio.Ui(p.Kind == Pressures.Grievance || p.Kind == Pressures.Demand ? "dread" : "page");
            }
        }

        bool Fire(Pressure p)
        {
            var mill = _gossip != null ? _gossip.Mill : null;
            if (mill == null) return false;

            switch (p.Kind)
            {
                case Pressures.Rumor:
                {
                    // The ordinary Witness path at low confidence: it decays, it
                    // spreads, it can be denied. The Director cannot plant a
                    // certainty any more than the player can.
                    if (mill.Get(p.Who) == null) return false;
                    mill.Witness(p.Who, new Fact("player", $"director_d{p.FireDay}", p.Line),
                        p.Line, sensitive: false, now: Now, confidence: 0.35);
                    return true;
                }

                case Pressures.Grievance:
                {
                    var g = mill.Get(p.Who);
                    if (g == null) return false;
                    g.Loyalty = Mathf.Clamp01((float)(g.Loyalty - p.Magnitude));
                    var host = _hosts.FirstOrDefault(h => h != null && h.Card != null && h.Card.Name == p.Who);
                    host?.Suspicion?.Raise(p.Magnitude * 0.5, p.Because);
                    g.Memory.Append(new MemoryEvent(Now, "observation", 0.75, p.Line));
                    return true;
                }

                case Pressures.Demand:
                {
                    if (mill.Get(p.Who) == null) return false;
                    if (DemandFrom(p.Who) != null) return false;     // one at a time, per person
                    Demands.Add(new OpenDemand
                    {
                        Who = p.Who, Amount = p.Amount,
                        DueDay = DirectorBook.DemandDueDay(p.FireDay, Now.Day), // always a window, never a countdown — even fired late
                        Line = p.Line,
                    });
                    return true;
                }

                case Pressures.Schedule:
                {
                    var walker = _npcs.FirstOrDefault(n => n != null && n.DisplayName == p.Who);
                    if (walker == null) return false;
                    // Somewhere they would not normally be: the bar, at the hour
                    // named. Being out of place is the whole content of this one.
                    walker.SetDetour(WorldBuilder.BarDoor + new Vector3(1.5f, 0, -1.5f),
                        Now.Day, 3, p.Hour, Mathf.Min(24, p.Hour + 3));
                    return true;
                }

                case Pressures.Meeting:
                {
                    var a = _npcs.FirstOrDefault(n => n != null && n.DisplayName == p.Who);
                    var b = _npcs.FirstOrDefault(n => n != null && n.DisplayName == p.Other);
                    if (a == null || b == null) return false;
                    // The collision Act II wants, made systemic: put the second
                    // person where the first one's routine already has them, so
                    // it happens somewhere that means something.
                    var at = new GameTime(Now.Day, p.Hour, 0);
                    b.SetDetour(a.RoutinePosition(at), Now.Day, 1, p.Hour, Mathf.Min(24, p.Hour + 2));
                    // And they will have been in a room together, which the
                    // gossip system already knows what to do with.
                    var ga = mill.Get(p.Who);
                    var gb = mill.Get(p.Other);
                    ga?.Memory.Append(new MemoryEvent(at, "observation", 0.7,
                        $"{p.Other} was there. We ended up in the same room."));
                    gb?.Memory.Append(new MemoryEvent(at, "observation", 0.7,
                        $"{p.Who} was there. We ended up in the same room."));
                    return true;
                }
            }
            return false;
        }

        /// CI seam. The build machine has no API key, so the Director never
        /// speaks there and its firing path would otherwise go untested every
        /// build — which is exactly the code most likely to break. This stages a
        /// pressure and runs it through the real primitives immediately, so the
        /// whole path is exercised in-engine whether or not a model was reachable.
        public bool StagePressure(Pressure p)
        {
            if (p == null || !p.IsSomething) return false;
            if (!Fire(p)) return false;
            Directorate.History.Add(p.Line);
            _ui?.Toast(p.Line, 12f);
            return true;
        }

        /// A demand nobody answered. Not a failure state — a grievance, which is
        /// how everything else in this game works.
        void CheckDemands()
        {
            for (int i = Demands.Count - 1; i >= 0; i--)
            {
                var d = Demands[i];
                if (Now.Day <= d.DueDay) continue;
                Demands.RemoveAt(i);
                var g = _gossip?.Mill?.Get(d.Who);
                if (g == null) continue;
                g.Loyalty = Mathf.Clamp01((float)(g.Loyalty - 0.2));
                g.Memory.Append(new MemoryEvent(Now, "observation", 0.85,
                    $"I asked for £{d.Amount}. The day came and went and I did not get it, and nothing was said about it."));
                _ui?.Toast($"{d.Who} stopped asking. That is not the same as letting it go.", 11f);
                Directorate.History.Add($"{d.Who}'s asking went unanswered.");
            }
        }

        // ---------------------------------------------------------------
        // 4. Persistence (pillar P5)
        // ---------------------------------------------------------------

        List<object> CaptureDemands()
        {
            var list = new List<object>();
            foreach (var d in Demands)
                list.Add(new Dictionary<string, object>
                {
                    { "who", d.Who }, { "amount", d.Amount }, { "dueDay", d.DueDay }, { "line", d.Line },
                });
            return list;
        }

        void RestoreDemands(List<object> list)
        {
            Demands.Clear();
            if (list == null) return;
            foreach (var raw in list)
            {
                var o = MiniJson.AsObject(raw);
                if (o == null) continue;
                var who = MiniJson.GetString(o, "who");
                if (string.IsNullOrEmpty(who)) continue;
                Demands.Add(new OpenDemand
                {
                    Who = who,
                    // Clamped on the way back in too: a save is untrusted input.
                    Amount = Mathf.Clamp(MiniJson.GetInt(o, "amount"), 0, Director.MaxDemand),
                    DueDay = MiniJson.GetInt(o, "dueDay"),
                    Line = MiniJson.GetString(o, "line") ?? "",
                });
            }
        }

        /// Settle a demand — the mechanical half, on GameController so the
        /// button, the router and any future caller share one implementation.
        public bool SettleDemand(string who, out string line)
        {
            line = null;
            var d = DemandFrom(who);
            if (d == null) return false;
            if (!Wallet.Spend(d.Amount, dirtyOk: true))
            {
                line = $"{who} named £{d.Amount}. You do not have it, and you both know it.";
                return false;
            }
            Demands.Remove(d);
            var g = _gossip?.Mill?.Get(who);
            if (g != null)
            {
                g.Loyalty = Mathf.Clamp01((float)(g.Loyalty + 0.15));
                g.Memory.Append(new MemoryEvent(Now, "observation", 0.8,
                    $"I asked for £{d.Amount} and it was there when I asked. That is not nothing."));
            }
            Audio.Ui("coin");
            line = $"£{d.Amount}, counted out where {who} can see it. Nobody says thank you, and it still counts.";
            return true;
        }
    }
}
