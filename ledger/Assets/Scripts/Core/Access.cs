using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// Access as soft keys (roadmap M7.5, agency-model dimension 65).
    ///
    /// Hitman's lesson, which is the best one in games about doors: a locked
    /// door is a wall, and a wall is not a decision. What makes a place
    /// interesting is that there are FOUR WAYS IN and each costs you something
    /// different. So nothing here is locked. Every gate lists several keys, and
    /// holding ANY of them opens it — which is also how this project's law of
    /// multiple solutions per obstacle gets enforced structurally rather than
    /// remembered case by case.
    ///
    /// The keys are all things the simulation already tracks: how you stand with
    /// an organization, how loudly the street talks about you, what you are
    /// wearing, whether somebody vouched for you, money, the hour, leverage, and
    /// how many people you brought. None of them is an item in a bag.
    ///
    /// AND A REFUSAL IS A PERSON TALKING. Never "ACCESS DENIED", never a red
    /// padlock. Somebody says no, in their own words, and — this is the part
    /// that makes it a system rather than a wall — the game names the NEAREST
    /// MISS, so a player who is turned away learns what would have worked.
    /// A door you cannot open and cannot learn about is just level geometry.

    public enum KeyKind
    {
        /// Standing with a named organization, as a percentage.
        Standing,
        /// The street's talk about you must be UNDER the named percentage.
        Quiet,
        /// The street's talk about you must be OVER it — some rooms only open
        /// to people who are already somebody.
        Notorious,
        /// What you are wearing: "coat" or "plain".
        Dress,
        /// Somebody vouched for you.
        Introduction,
        /// Money, and it is spent.
        Payment,
        /// It must be at or after this hour.
        After,
        /// It must be before this hour.
        Before,
        /// You hold something over the person on the door.
        Hook,
        /// You brought this many people.
        Crew,
    }

    /// One way in. A gate holds several; any one of them is enough.
    public class AccessKey
    {
        public KeyKind Kind;
        /// Which organization, for Standing. Which person, for Introduction.
        public string Who;
        /// Percentage, money, hour or headcount, depending on Kind.
        public int Amount;
        /// For Dress: "coat" or "plain".
        public string Dress;
        /// How this way in reads when it is the one that worked, and when it is
        /// the one you ALMOST had. Both in the doorman's voice.
        public string Opens;
        public string Nearly;

        public AccessKey() { }
        public AccessKey(KeyKind kind, int amount = 0, string who = null, string dress = null)
        {
            Kind = kind; Amount = amount; Who = who; Dress = dress;
        }

        public AccessKey Reads(string opens, string nearly)
        {
            Opens = opens; Nearly = nearly;
            return this;
        }

        /// How far short you are, 0 = held, 1 = nowhere near. Used to pick which
        /// near-miss to tell the player about, so the hint is the useful one
        /// rather than the first one in the list.
        public double ShortfallFrom(AccessState s)
        {
            if (s == null) return 1;
            switch (Kind)
            {
                case KeyKind.Standing:
                {
                    double have = s.StandingWith(Who) * 100.0;
                    return have >= Amount ? 0 : Clamp01((Amount - have) / Math.Max(1.0, Amount + 100.0));
                }
                case KeyKind.Quiet:
                {
                    double have = s.Notoriety * 100.0;
                    return have <= Amount ? 0 : Clamp01((have - Amount) / 100.0);
                }
                case KeyKind.Notorious:
                {
                    double have = s.Notoriety * 100.0;
                    return have >= Amount ? 0 : Clamp01((Amount - have) / Math.Max(1.0, Amount));
                }
                case KeyKind.Dress:
                    return string.Equals(s.Dress, Dress, StringComparison.OrdinalIgnoreCase) ? 0 : 0.5;
                case KeyKind.Introduction:
                    return s.HasIntroduction(Who) ? 0 : 0.7;
                case KeyKind.Payment:
                    return s.Money >= Amount ? 0
                        : Clamp01((Amount - s.Money) / (double)Math.Max(1, Amount));
                case KeyKind.After:
                    return s.Hour >= Amount ? 0 : Clamp01((Amount - s.Hour) / 24.0);
                case KeyKind.Before:
                    return s.Hour < Amount ? 0 : Clamp01((s.Hour - Amount) / 24.0);
                case KeyKind.Hook:
                    return s.HoldsHookOnDoor ? 0 : 0.8;
                case KeyKind.Crew:
                    return s.Crew >= Amount ? 0 : Clamp01((Amount - s.Crew) / (double)Math.Max(1, Amount));
                default:
                    return 1;
            }
        }

        public bool Held(AccessState s) => ShortfallFrom(s) <= 0;

        static double Clamp01(double v) => v < 0 ? 0 : v > 1 ? 1 : v;
    }

    /// A place or a person you have to get past.
    public class Gate
    {
        public string Id;
        public string Name;
        /// Who is standing there saying no. A door with nobody on it is a wall.
        public string Doorman;
        public readonly List<AccessKey> Keys = new List<AccessKey>();
        /// The refusal when nothing is even close. In the doorman's voice.
        public string Refusal = "Not tonight.";

        public Gate() { }
        public Gate(string id, string name, string doorman = null)
        {
            Id = id; Name = name; Doorman = doorman;
        }

        public Gate WithKey(AccessKey key)
        {
            if (key != null) Keys.Add(key);
            return this;
        }
    }

    /// Everything a gate is allowed to look at. Assembled from live state.
    public class AccessState
    {
        /// Standing with each organization, -1..1.
        public readonly Dictionary<string, double> Standing =
            new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        /// How loudly the street talks about you, 0..1.
        public double Notoriety;
        /// "coat" or "plain".
        public string Dress = "plain";
        public readonly HashSet<string> Introductions =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        public int Money;
        public int Hour;
        public int Crew;
        /// Whether you hold something over whoever is on this particular door.
        public bool HoldsHookOnDoor;

        public double StandingWith(string who) =>
            who != null && Standing.TryGetValue(who, out var v) ? v : 0.0;

        public bool HasIntroduction(string who) =>
            who != null && Introductions.Contains(who);
    }

    public class AccessResult
    {
        public bool Allowed;
        /// The key that opened it, or null.
        public AccessKey Used;
        /// What the player is told, either way. Always somebody talking.
        public string Line = "";
        /// On refusal: the way in you came closest to having.
        public AccessKey Nearest;
        /// On refusal: what that near miss would have taken, in plain words.
        public string Hint = "";
        /// What it cost, if the key that worked was a payment.
        public int Paid;
    }

    public static class Doors
    {
        /// Evaluates a gate. Prefers the CHEAPEST key held rather than the first
        /// listed — a player who has both an introduction and forty dollars
        /// should not silently spend the forty dollars.
        public static AccessResult Try(Gate gate, AccessState state)
        {
            var result = new AccessResult();
            if (gate == null || state == null)
            {
                result.Line = "There is nothing here to go into.";
                return result;
            }
            if (gate.Keys.Count == 0)
            {
                // A gate with no keys is a wall, and walls are a design failure
                // rather than a difficulty setting. Open it and say nothing.
                result.Allowed = true;
                result.Line = "";
                return result;
            }

            var held = gate.Keys.Where(k => k.Held(state)).ToList();
            if (held.Count > 0)
            {
                var chosen = held.OrderBy(CostRank).ThenBy(k => (int)k.Kind).First();
                result.Allowed = true;
                result.Used = chosen;
                result.Paid = chosen.Kind == KeyKind.Payment ? chosen.Amount : 0;
                result.Line = !string.IsNullOrEmpty(chosen.Opens) ? chosen.Opens : DefaultOpens(gate, chosen);
                return result;
            }

            // Refused. Find the way in they came closest to, and say what it
            // would have taken — a door you cannot learn about is level geometry.
            var nearest = gate.Keys.OrderBy(k => k.ShortfallFrom(state)).First();
            result.Nearest = nearest;
            result.Line = gate.Refusal;
            result.Hint = !string.IsNullOrEmpty(nearest.Nearly) ? nearest.Nearly : DefaultNearly(nearest, state);
            return result;
        }

        /// Free ways in are preferred over ones that cost you something, and
        /// among costly ones, the one that costs least.
        static int CostRank(AccessKey k)
        {
            switch (k.Kind)
            {
                case KeyKind.Introduction: return 0;   // already paid for, socially
                case KeyKind.Standing: return 1;
                case KeyKind.Notorious: return 1;
                case KeyKind.Dress: return 1;
                case KeyKind.After:
                case KeyKind.Before: return 1;
                case KeyKind.Quiet: return 1;
                case KeyKind.Crew: return 2;           // costs their time and visibility
                case KeyKind.Hook: return 3;           // spends leverage you could keep
                case KeyKind.Payment: return 4;        // spends money, always last
                default: return 5;
            }
        }

        static string DefaultOpens(Gate gate, AccessKey k)
        {
            var who = gate.Doorman ?? "The man on the door";
            switch (k.Kind)
            {
                case KeyKind.Introduction: return $"{who} hears whose name you say and stands aside.";
                case KeyKind.Standing:     return $"{who} knows who you run with. That is enough tonight.";
                case KeyKind.Notorious:    return $"{who} recognises you, and decides not to be the one who stopped you.";
                case KeyKind.Dress:        return $"{who} looks at what you are wearing and loses interest in you.";
                case KeyKind.Quiet:        return $"{who} has not heard anything about you. That is the whole test.";
                case KeyKind.Payment:      return $"{who} takes the money without looking at it.";
                case KeyKind.Crew:         return $"{who} counts the people behind you and does the arithmetic.";
                case KeyKind.Hook:         return $"{who} meets your eye, remembers what you know, and looks away.";
                // The two hour keys used to fall through to the flat default,
                // which is the wrong line for exactly the doors where the CLOCK
                // is the whole content of being let in.
                case KeyKind.After:        return $"{who} checks the hour without hurrying. Whatever this room is before now, it is something else after.";
                case KeyKind.Before:       return $"{who} waves you through. Another twenty minutes and he would have been locking up.";
                default:                   return $"{who} lets you past.";
            }
        }

        static string DefaultNearly(AccessKey k, AccessState s)
        {
            switch (k.Kind)
            {
                case KeyKind.Introduction:
                    return $"Somebody would have to speak for you. {k.Who} would do it, if {k.Who} liked you more.";
                case KeyKind.Standing:
                    return $"You would need to stand better with {k.Who} than you do.";
                case KeyKind.Notorious:
                    return "Nobody in there has heard of you yet.";
                case KeyKind.Quiet:
                    return "Too many people are saying your name this week.";
                case KeyKind.Dress:
                    return k.Dress == "coat"
                        ? "You would not be recognised so easily with the coat on."
                        : "The coat is the problem. In there, it is the wrong thing to be wearing.";
                case KeyKind.Payment:
                    return $"It would take ${k.Amount}, and you have ${s.Money}.";
                case KeyKind.After:
                    return $"Not before {k.Amount}. Come back when it is dark enough.";
                case KeyKind.Before:
                    return $"You have left it too late. Before {k.Amount}, and not after.";
                case KeyKind.Hook:
                    return "If you had something on him, this would be a different conversation.";
                case KeyKind.Crew:
                    return k.Amount == 1
                        ? "Not on your own."
                        : $"You would want {k.Amount} people behind you, and you have {s.Crew}.";
                default:
                    return "";
            }
        }
    }
}
