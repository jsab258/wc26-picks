using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Ledger.Core
{
    /// The Director (roadmap M8, design doc §17 gap 2).
    ///
    /// Act I's pressure points and Act II's Squeeze are authored beats that fire
    /// on state conditions. That is a real improvement over dated beats, and it
    /// is still finite: the pressure a player feels on day 30 was written by us
    /// on day 1, and there are only so many of them.
    ///
    /// This is a nightly pass at the WORLD level — not the character level —
    /// that reads the actual state (who is angry, who is exposed, what the
    /// player has been ignoring, which relationships are load-bearing, what the
    /// street's money is doing) and authors the next pressure from it.
    ///
    /// THE LAW IS THE ROUTER'S LAW. The Director proposes; it never adjudicates.
    /// It may only ask for a pressure assembled from primitives the game already
    /// has — put a fact in the mill, arrange a meeting, make a demand, change
    /// where somebody is, seed a grievance — and every person it names must
    /// exist in the snapshot it was given. Anything else is rejected whole. The
    /// simulation then runs the pressure exactly as it runs an authored one, so
    /// the Director cannot invent an outcome, only an occasion.
    ///
    /// Authored anchors still exist and still fire. This fills the enormous
    /// space between them, which today is empty.

    /// What the Director is allowed to ask for. Anything outside this set is
    /// not a pressure, it is a hallucination, and is discarded.
    public static class Pressures
    {
        /// Somebody starts carrying a story about the player. Enters through the
        /// ordinary Witness path at low confidence, so it decays and can be
        /// contradicted like anything else the street half-saw.
        public const string Rumor = "rumor";
        /// Two people end up in the same room at the same hour. Act II's set
        /// pieces are systemic collisions; this is the machine that makes them.
        public const string Meeting = "meeting";
        /// Somebody wants something from the player by a given day: money, or a
        /// favour. Becomes a real obligation with a real window.
        public const string Demand = "demand";
        /// Somebody's routine changes for a few days, for a reason.
        public const string Schedule = "schedule";
        /// Somebody's feeling about the player moves, because of something
        /// specific that actually happened.
        public const string Grievance = "grievance";
        /// The correct answer most nights, and the one the prompt argues for.
        public const string Nothing = "nothing";

        public static readonly string[] All = { Rumor, Meeting, Demand, Schedule, Grievance, Nothing };
        public static bool Known(string s) => s != null && All.Contains(s);
    }

    /// One person as the Director sees them: a name, how they feel, and one
    /// line of why that might matter tonight.
    public class WorldPerson
    {
        public string Name;
        public string Role;        // "bookkeeper", "crew", "rival head", "supplier"
        public double Loyalty;
        public double Suspicion;
        public string Note;        // "hasn't been paid in three weeks"

        public WorldPerson() { }
        public WorldPerson(string name, string role, double loyalty, double suspicion, string note = null)
        {
            Name = name; Role = role; Loyalty = loyalty; Suspicion = suspicion; Note = note;
        }
    }

    /// Everything the Director is allowed to know. Assembled from live state by
    /// the game each night; nothing else reaches the model.
    public class WorldSnapshot
    {
        public int Day;
        public double Heat;
        /// The street's money, in the words the economy uses: "hurting, prices steep".
        public string Street = "";
        public readonly List<WorldPerson> People = new List<WorldPerson>();
        /// What the player has left undone — the richest source of real pressure.
        public readonly List<string> Ignored = new List<string>();
        /// The last few days, one line each.
        public readonly List<string> Recent = new List<string>();
        /// Pressures already in flight. The Director must not stack.
        public readonly List<string> InFlight = new List<string>();

        public bool Knows(string name) =>
            !string.IsNullOrEmpty(name) &&
            People.Any(p => string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase));

        public WorldPerson PersonNamed(string name) =>
            People.FirstOrDefault(p => string.Equals(p.Name, name, StringComparison.OrdinalIgnoreCase));
    }

    /// A validated pressure, waiting for its day.
    public class Pressure
    {
        public string Kind = Pressures.Nothing;
        /// Whose pressure this is. Always a name from the snapshot.
        public string Who;
        /// The second person, for a meeting. Always a name from the snapshot.
        public string Other;
        public int FireDay;
        /// What the player sees when it lands, in the world's voice.
        public string Line = "";
        /// The state the Director read to justify it — kept for the debug panel
        /// and for judging whether the Director is actually reading anything.
        public string Because = "";
        /// For a demand: what is being asked for, in money.
        public int Amount;
        /// For a grievance: how far the feeling moves. Clamped.
        public double Magnitude;
        /// For a schedule or meeting: the hour it happens.
        public int Hour = 20;

        public bool IsSomething => Kind != Pressures.Nothing;

        public override string ToString() =>
            IsSomething ? $"{Kind}:{Who}{(Other != null ? "+" + Other : "")}@d{FireDay}" : "nothing";
    }

    public class Director
    {
        readonly ILlmClient _llm;
        readonly CostTracker _cost;
        public string Model { get; set; } = Models.Core;

        /// A pressure lands no sooner than tomorrow and no later than this,
        /// so the player always has a day to see it coming.
        public int MinLead = 1;
        public int MaxLead = 4;
        /// The Director is not a metronome. Two pressures may be in flight; a
        /// third is refused however good the reason, because an authored spine
        /// plus a busy Director is just noise.
        public int MaxInFlight = 2;
        public int MinDaysBetween = 3;
        /// A grievance is a nudge, never a verdict — the same ceiling the
        /// router's novel actions live under, for the same reason.
        public const double MaxMagnitude = 0.2;
        /// A demand the player could never meet is not pressure, it is an
        /// ending. Bounded to something a working week can cover.
        public const int MaxDemand = 800;

        public Director(ILlmClient llm = null, CostTracker cost = null)
        {
            _llm = llm;
            _cost = cost;
        }

        /// Whether tonight is a night the Director gets to speak at all. Cheap,
        /// deterministic, and checked BEFORE any call is made — most nights the
        /// answer is no and no tokens are spent.
        public bool ShouldRun(WorldSnapshot world, int lastRunDay)
        {
            if (world == null) return false;
            if (world.InFlight.Count >= MaxInFlight) return false;
            if (lastRunDay >= 0 && world.Day - lastRunDay < MinDaysBetween) return false;
            // Nothing to read from is nothing to write from.
            return world.People.Count > 0;
        }

        public async Task<Pressure> ProposeAsync(WorldSnapshot world, CancellationToken ct = default)
        {
            if (_llm == null || world == null) return new Pressure();

            var request = new LlmRequest
            {
                Model = Model,
                System = BuildPrompt(world),
                MaxTokens = 400,
            };
            request.Messages.Add(new LlmMessage("user",
                $"It is the end of day {world.Day}. Read the state above and decide what happens next, if anything."));

            LlmResponse response;
            try { response = await _llm.CompleteAsync(request, ct); }
            catch (Exception) { return new Pressure(); }   // a silent night is always safe

            _cost?.Record(Model, response.InputTokens, response.OutputTokens);
            return Validate(response.Text, world);
        }

        public string BuildPrompt(WorldSnapshot world)
        {
            var sb = new StringBuilder();
            sb.AppendLine("You are the director of a crime and social simulation. Once every few in-game nights you");
            sb.AppendLine("read the state of one street and decide what pressure the world applies next.");
            sb.AppendLine("You do not decide outcomes. You schedule an occasion; the simulation runs it.");
            sb.AppendLine();
            sb.AppendLine($"END OF DAY {world.Day}.");
            sb.AppendLine($"Talk about the player on the street: {Heatword(world.Heat)}.");
            if (!string.IsNullOrEmpty(world.Street)) sb.AppendLine($"The street's money: {world.Street}.");
            sb.AppendLine();

            sb.AppendLine("PEOPLE (you may only name these):");
            foreach (var p in world.People)
            {
                sb.Append("- ").Append(p.Name).Append(" (").Append(p.Role).Append("): ");
                sb.Append(Feeling(p.Loyalty, p.Suspicion));
                if (!string.IsNullOrEmpty(p.Note)) sb.Append("; ").Append(p.Note);
                sb.AppendLine();
            }
            sb.AppendLine();

            if (world.Ignored.Count > 0)
            {
                sb.AppendLine("WHAT THE PLAYER HAS LEFT UNDONE — this is usually where the pressure is:");
                foreach (var i in world.Ignored) sb.AppendLine("- " + i);
                sb.AppendLine();
            }
            if (world.Recent.Count > 0)
            {
                sb.AppendLine("RECENTLY:");
                foreach (var r in world.Recent) sb.AppendLine("- " + r);
                sb.AppendLine();
            }
            if (world.InFlight.Count > 0)
            {
                sb.AppendLine("ALREADY COMING (do not repeat or stack onto these):");
                foreach (var f in world.InFlight) sb.AppendLine("- " + f);
                sb.AppendLine();
            }

            sb.AppendLine("WHAT YOU MAY SCHEDULE. These are the only kinds that exist:");
            sb.AppendLine($"- \"{Pressures.Rumor}\": one named person starts saying something about the player. Low confidence — it can be denied and it will fade if nobody feeds it.");
            sb.AppendLine($"- \"{Pressures.Meeting}\": two named people end up in the same place at the same hour. Use this when two parts of the player's life should collide.");
            sb.AppendLine($"- \"{Pressures.Demand}\": one named person wants money from the player by a given day. At most ${MaxDemand}.");
            sb.AppendLine($"- \"{Pressures.Schedule}\": one named person is somewhere unusual at a given hour for a few days.");
            sb.AppendLine($"- \"{Pressures.Grievance}\": one named person's feeling about the player moves, because of something specific that already happened.");
            sb.AppendLine($"- \"{Pressures.Nothing}\": nothing happens. THIS IS USUALLY CORRECT. A world that produces an event every few days is a soap opera, not a place.");
            sb.AppendLine();
            sb.AppendLine("Reply with one JSON object and nothing else:");
            sb.AppendLine("{\"kind\":\"<kind>\",\"who\":\"<name>\",\"other\":\"<name, meeting only>\",");
            sb.AppendLine($" \"day\":<{world.Day + MinLead}..{world.Day + MaxLead}>,\"hour\":<0..23>,\"amount\":<money, demand only>,");
            sb.AppendLine(" \"magnitude\":<0..0.2, grievance only>,");
            sb.AppendLine(" \"line\":\"<one or two sentences the player reads when it lands, in plain past tense, no stage directions>\",");
            sb.AppendLine(" \"because\":\"<the specific thing in the state above that justifies it>\"}");
            sb.AppendLine();
            sb.AppendLine("Rules:");
            sb.AppendLine("- Never name a person who is not in the list above.");
            sb.AppendLine("- \"because\" must point at something concrete in the state — a name, a number, a thing left undone. If you cannot, the answer is \"nothing\".");
            sb.AppendLine("- Pressure comes from what the player neglected, not from bad luck. Do not invent a stranger, an accident, or a coincidence.");
            sb.AppendLine("- Write \"line\" the way a person tells you what happened, plainly. No dashes, no lists of three, no words like tapestry, testament, delve, pivotal.");
            return sb.ToString();
        }

        /// The boundary, and it is the same joyless boundary the router uses:
        /// unknown kind, unknown person, or a day outside the window and the
        /// whole proposal becomes a quiet night. Nothing is coerced into
        /// validity — a pressure is exactly right or it did not happen.
        public Pressure Validate(string raw, WorldSnapshot world)
        {
            var json = IntentRouter.ExtractJson(raw);
            if (json == null || world == null) return new Pressure();

            Dictionary<string, object> obj;
            try { obj = MiniJson.AsObject(MiniJson.Deserialize(json)); }
            catch (Exception) { return new Pressure(); }
            if (obj == null) return new Pressure();

            var kind = (MiniJson.GetString(obj, "kind") ?? "").Trim().ToLowerInvariant();
            if (!Pressures.Known(kind) || kind == Pressures.Nothing) return new Pressure();

            var who = (MiniJson.GetString(obj, "who") ?? "").Trim();
            var whoPerson = world.PersonNamed(who);
            if (whoPerson == null) return new Pressure();       // named a stranger

            int day = MiniJson.GetInt(obj, "day");
            if (day < world.Day + MinLead || day > world.Day + MaxLead) return new Pressure();

            var line = (MiniJson.GetString(obj, "line") ?? "").Trim();
            if (line.Length == 0) return new Pressure();        // an occasion nobody can see is not one
            line = ConversationEngine.ValidateReply(line);      // same scrubbing every NPC line gets

            var because = (MiniJson.GetString(obj, "because") ?? "").Trim();
            if (because.Length == 0) return new Pressure();     // unjustified is unwanted

            var p = new Pressure
            {
                Kind = kind,
                Who = whoPerson.Name,                            // the snapshot's spelling, not the model's
                FireDay = day,
                Line = line,
                Because = because.Length > 160 ? because.Substring(0, 160) : because,
                Hour = Math.Clamp(MiniJson.GetInt(obj, "hour"), 0, 23),
            };

            if (kind == Pressures.Meeting)
            {
                var other = world.PersonNamed((MiniJson.GetString(obj, "other") ?? "").Trim());
                if (other == null || other.Name == p.Who) return new Pressure();
                p.Other = other.Name;
            }
            else if (kind == Pressures.Demand)
            {
                p.Amount = Math.Clamp(MiniJson.GetInt(obj, "amount"), 1, MaxDemand);
            }
            else if (kind == Pressures.Grievance)
            {
                p.Magnitude = ClampMagnitude(obj);
                if (p.Magnitude <= 0) return new Pressure();     // a grievance that moves nothing is noise
            }

            return p;
        }

        static double ClampMagnitude(Dictionary<string, object> obj)
        {
            double m = 0;
            if (obj.TryGetValue("magnitude", out var v) && v != null)
            {
                if (v is double d) m = d;
                else if (v is long l) m = l;
                else if (v is int i) m = i;
                else double.TryParse(Convert.ToString(v, System.Globalization.CultureInfo.InvariantCulture),
                    System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out m);
            }
            if (double.IsNaN(m) || double.IsInfinity(m)) return 0;
            return Math.Max(0, Math.Min(MaxMagnitude, m));
        }

        static string Heatword(double h) =>
            h >= 0.7 ? "loud" : h >= 0.45 ? "steady" : h >= 0.2 ? "quiet" : "almost nothing";

        static string Feeling(double loyalty, double suspicion)
        {
            var l = loyalty >= 0.7 ? "loyal" : loyalty >= 0.45 ? "friendly" : loyalty >= 0.25 ? "cool" : "done with you";
            var s = suspicion >= 0.7 ? "and openly suspicious" : suspicion >= 0.4 ? "and wondering about you" : "and not suspicious";
            return l + ", " + s;
        }
    }

    /// The pressures the Director has scheduled and the game has not yet run.
    /// Persisted like everything else — pillar P5, the city's state is the save.
    public class DirectorBook
    {
        public readonly List<Pressure> Pending = new List<Pressure>();
        public int LastRunDay = -1;
        /// Everything that has ever fired, one line each, for the ledger panel.
        public readonly List<string> History = new List<string>();

        public void Schedule(Pressure p)
        {
            if (p == null || !p.IsSomething) return;
            Pending.Add(p);
        }

        /// The day a demand handed out today falls due. Always a window, never
        /// a countdown — and the window opens from the day the demand actually
        /// REACHES the player, not the day it was scheduled to. The difference
        /// bit once: the Fall skips three calendar days, so a demand scheduled
        /// inside the skipped window fired at the first post-Fall close with
        /// its due day already in the past, and the player took the ignored-it
        /// loyalty penalty for a window that never existed (audit 2026-07-27).
        public static int DemandDueDay(int scheduledFireDay, int todayDay) =>
            Math.Max(scheduledFireDay, todayDay) + 2;

        /// Pressures whose day has come. Removed as they are handed out, so a
        /// pressure fires exactly once however often this is polled.
        public List<Pressure> Due(GameTime now)
        {
            var due = Pending.Where(p => p.FireDay <= now.Day).ToList();
            foreach (var p in due) Pending.Remove(p);
            return due;
        }

        public List<string> InFlightLines() =>
            Pending.Select(p => $"{p.Kind} involving {p.Who}{(p.Other != null ? " and " + p.Other : "")} on day {p.FireDay}")
                   .ToList();

        public Dictionary<string, object> Capture()
        {
            var list = new List<object>();
            foreach (var p in Pending)
                list.Add(new Dictionary<string, object>
                {
                    { "kind", p.Kind }, { "who", p.Who }, { "other", p.Other },
                    { "fireDay", p.FireDay }, { "hour", p.Hour }, { "amount", p.Amount },
                    { "magnitude", p.Magnitude }, { "line", p.Line }, { "because", p.Because },
                });
            return new Dictionary<string, object>
            {
                { "lastRunDay", LastRunDay }, { "pending", list },
                { "history", History.Cast<object>().ToList() },
            };
        }

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            Pending.Clear();
            History.Clear();
            LastRunDay = data.ContainsKey("lastRunDay") ? MiniJson.GetInt(data, "lastRunDay") : -1;

            var list = MiniJson.GetList(data, "pending");
            if (list != null)
                foreach (var raw in list)
                {
                    var o = MiniJson.AsObject(raw);
                    if (o == null) continue;
                    var kind = MiniJson.GetString(o, "kind");
                    if (!Pressures.Known(kind) || kind == Pressures.Nothing) continue;  // never trust a save either
                    Pending.Add(new Pressure
                    {
                        Kind = kind,
                        Who = MiniJson.GetString(o, "who"),
                        Other = MiniJson.GetString(o, "other"),
                        FireDay = MiniJson.GetInt(o, "fireDay"),
                        Hour = Math.Clamp(MiniJson.GetInt(o, "hour"), 0, 23),
                        Amount = Math.Clamp(MiniJson.GetInt(o, "amount"), 0, Director.MaxDemand),
                        Magnitude = Math.Clamp(GetD(o, "magnitude"), 0, Director.MaxMagnitude),
                        Line = MiniJson.GetString(o, "line") ?? "",
                        Because = MiniJson.GetString(o, "because") ?? "",
                    });
                }

            var hist = MiniJson.GetList(data, "history");
            if (hist != null)
                foreach (var h in hist)
                    if (h is string s) History.Add(s);
        }

        static double GetD(Dictionary<string, object> o, string key)
        {
            if (o == null || !o.TryGetValue(key, out var v) || v == null) return 0;
            if (v is double d) return d;
            if (v is long l) return l;
            if (v is int i) return i;
            return 0;
        }
    }
}
